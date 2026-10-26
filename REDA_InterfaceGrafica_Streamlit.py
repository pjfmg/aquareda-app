from hashlib import sha256
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from reda_queue import (FIELDS, STATES, PRIORITIES, text, load_workbook,
                        queue_view, export_workbook)

st.set_page_config(page_title='REDA — revisão local', layout='wide')
st.title('📚 REDA — catálogo e fila de revisão semanal')
st.info('Apoio à revisão humana. Não aprova, rejeita nem altera recursos nos sistemas oficiais.')
st.caption('Os dados ficam na sessão. Exporte o Excel para guardar e volte a carregá-lo para continuar noutra semana. Não existe agendamento automático.')
upload = st.file_uploader('Carregar Excel (.xlsx)', type=['xlsx'])
if upload:
    raw = upload.getvalue()
    try:
        sheets = pd.ExcelFile(BytesIO(raw), engine='openpyxl').sheet_names
    except Exception:
        st.error('Não foi possível abrir o Excel. Confirme que é um ficheiro .xlsx válido e não está protegido por palavra-passe.')
        st.stop()
    digest = sha256(raw).hexdigest()
    sheet = st.selectbox('Folha a importar', sheets, key=f'sheet_{digest}')
    restore = st.checkbox('Restaurar notas de uma exportação desta aplicação', value=False, key=f'restore_{digest}_{sheet}')
    identity = (digest, sheet, restore)
    if st.session_state.get('identity') != identity:
        try:
            source, notes, mapping, missing = load_workbook(raw, sheet, restore)
        except Exception as exc:
            if restore:
                st.warning('As notas não foram atribuídas. Conserve o ficheiro original e confira as duas folhas antes de tentar novamente.')
            st.error(f'Importação não concluída: {exc}')
            st.stop()
        st.session_state.update(identity=identity, source=source, notes=notes, mapping=mapping, missing=missing)
    source, notes = st.session_state.source, st.session_state.notes
    mapping, missing = st.session_state.mapping, st.session_state.missing
    prefix = f'{digest}_{sheet}_{restore}'
    st.write(f'{len(source)} recursos carregados. Colunas disponíveis: ' + ', '.join(map(str, source.columns)))
    if missing:
        st.warning('Campos não identificados: ' + ', '.join(missing) + '. Pode associar colunas ou criar campos vazios abaixo. Campos vazios requerem confirmação; nem todos serão aplicáveis a cada recurso.')
    with st.expander('Associar campos do catálogo às colunas existentes'):
        for field in FIELDS:
            options = [None] + list(source.columns)
            chosen = st.selectbox(field, options, index=options.index(mapping.get(field)), format_func=lambda v: 'Não disponível' if v is None else str(v), key=f'{prefix}_map_{st.session_state.get("map_generation", 0)}_{field}')
            if chosen is None:
                mapping.pop(field, None)
            else:
                mapping[field] = chosen
        if st.button('Criar campos do catálogo em falta, vazios'):
            for field in FIELDS:
                if field not in mapping and field not in source.columns:
                    source[field] = ''
                    mapping[field] = field
            st.session_state.map_generation = st.session_state.get('map_generation', 0) + 1
            st.session_state.missing = [f for f in FIELDS if f not in mapping]
            st.rerun()
    if len(set(mapping.values())) != len(mapping):
        st.error('Associe uma coluna diferente a cada campo do catálogo para evitar sobrepor edições.')
        st.stop()
    opts = [None] + list(source.columns)
    date_col = st.selectbox('Coluna com a data do pedido (confirme o significado)', opts, format_func=lambda v: 'Não selecionada' if v is None else str(v), key=f'{prefix}_date')
    state_col = st.selectbox('Coluna com o estado na fonte (apenas informativo)', opts, format_func=lambda v: 'Não selecionada' if v is None else str(v), key=f'{prefix}_state')
    old_days = st.number_input('Destacar pedidos com pelo menos este número de dias', min_value=1, value=30, key=f'{prefix}_old')
    st.caption('Regra de destaque ajustável, sem prazo oficial presumido. Datas de texto: AAAA-MM-DD, DD/MM/AAAA ou DD-MM-AAAA. Datas ausentes, futuras ou não reconhecidas ficam por confirmar.')
    today = datetime.now(ZoneInfo('Atlantic/Azores')).date()
    view = queue_view(source, notes, mapping, date_col, state_col, today, old_days)
    st.subheader('Fila local')
    show_completed = st.checkbox('Mostrar também revisões locais concluídas', value=False, key=f'{prefix}_completed')
    visible = view if show_completed else view[view['ESTADO LOCAL'] != 'Revisão local concluída']
    st.caption('Ordem: prioridade introduzida manualmente; depois, maior antiguidade conhecida. Sem prioridade: por classificar. Estado na fonte e estado local são independentes.')
    st.dataframe(visible, hide_index=True)
    st.subheader('Revisão manual')
    for i in visible.index:
        resource_id = notes.at[i, 'ID LOCAL']
        with st.expander(view.at[i, 'TÍTULO / REFERÊNCIA']):
            st.caption(f'Linha Excel {i + 2} — ID local {resource_id}')
            for field in ['ESTADO LOCAL', 'PRIORIDADE LOCAL']:
                choices = list(STATES if field == 'ESTADO LOCAL' else PRIORITIES)
                current = text(notes.at[i, field])
                if current not in choices:
                    choices.append(current)
                notes.at[i, field] = st.selectbox(field, choices, index=choices.index(current), format_func=lambda v: 'Por introduzir / confirmar' if v == '' else v, key=f'{prefix}_{resource_id}_{field}')
            for field in ['BLOQUEIOS', 'PRÓXIMO PASSO']:
                notes.at[i, field] = st.text_area(field, value=text(notes.at[i, field]), key=f'{prefix}_{resource_id}_{field}')
            st.caption('Edições do catálogo afetam apenas a cópia exportada. Dados em branco não significam ausência confirmada.')
            for field in FIELDS:
                if field in mapping:
                    column = mapping[field]
                    source.at[i, column] = st.text_input(field, value=text(source.at[i, column]), key=f'{prefix}_{resource_id}_catalog_{field}')
                else:
                    st.write(f'{field}: coluna não disponível; associe ou crie o campo acima.')
    if st.button('Atualizar fila após edição'):
        st.rerun()
    view = queue_view(source, notes, mapping, date_col, state_col, today, old_days)
    st.download_button('Guardar catálogo e revisão local em Excel', export_workbook(source, notes, view), 'REDA_Revisao_Local.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

