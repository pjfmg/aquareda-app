"""Importação e revisão local; sem ligação ou decisões em sistemas oficiais."""
from io import BytesIO
import unicodedata
import uuid
from datetime import date, datetime
from numbers import Number

import pandas as pd

FIELDS = ['TÍTULO', 'AUTOR/FONTE', 'ORGANIZAÇÃO', 'DURAÇÃO DO VÍDEO', 'CÓDIGO DE INCORPORAÇÃO']
NOTES = ['ID LOCAL', 'ESTADO LOCAL', 'PRIORIDADE LOCAL', 'BLOQUEIOS', 'PRÓXIMO PASSO']
STATES = ['', 'Por rever', 'Em revisão', 'A aguardar informação', 'Revisão local concluída']
PRIORITIES = ['', 'Urgente', 'Alta', 'Normal', 'Baixa']


def text(value):
    return '' if pd.isna(value) else str(value)


def normalized(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', str(value)) if not unicodedata.combining(c)).upper().split())


def field_mapping(frame):
    """Só correspondências exatas após normalizar acentos, caixa e espaços."""
    result = {}
    for field in FIELDS:
        matches = [c for c in frame.columns if normalized(c) == normalized(field)]
        if len(matches) == 1:
            result[field] = matches[0]
    return result


def new_notes(count):
    frame = pd.DataFrame('', index=range(count), columns=NOTES)
    frame['ID LOCAL'] = [str(uuid.uuid4()) for _ in range(count)]
    return frame


def load_workbook(data, sheet=0, restore=False):
    """A restauração é explícita, nunca inferida de uma folha de nome semelhante."""
    book = pd.ExcelFile(BytesIO(data), engine='openpyxl')
    source = pd.read_excel(book, sheet_name=sheet, dtype=object).reset_index(drop=True)
    if not source.columns.is_unique:
        raise ValueError('Existem colunas duplicadas; renomeie-as antes de importar.')
    notes = new_notes(len(source))
    if restore:
        if sheet != 'Recursos' or 'Revisao_local' not in book.sheet_names:
            raise ValueError('Selecione a folha Recursos de uma exportação desta aplicação.')
        saved = pd.read_excel(book, sheet_name='Revisao_local', dtype=object).fillna('')
        if list(saved.columns) != NOTES or len(saved) != len(source):
            raise ValueError('A revisão guardada não corresponde às linhas dos recursos.')
        ids = saved['ID LOCAL'].map(text)
        if ids.eq('').any() or ids.duplicated().any():
            raise ValueError('Identificadores locais inválidos ou repetidos.')
        notes = saved
    mapping = field_mapping(source)
    missing = [f for f in FIELDS if f not in mapping]
    return source, notes, mapping, missing


def parse_request_date(value):
    """Sem datas de importação substitutas nem números Excel adivinhados."""
    if pd.isna(value) or text(value).strip() == '':
        return None, 'Sem data'
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.date() if isinstance(value, (datetime, pd.Timestamp)) else value, ''
    if isinstance(value, Number):
        return None, 'Data numérica por confirmar'
    for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(str(value).strip(), fmt).date(), ''
        except ValueError:
            pass
    return None, 'Data inválida ou formato por confirmar'


def queue_view(source, notes, mapping, date_column=None, state_column=None, today=None, old_days=30):
    today = today or date.today()
    result = notes.copy()
    result['LINHA EXCEL'] = list(range(2, len(source) + 2))
    result['TÍTULO / REFERÊNCIA'] = [text(source.iloc[i][mapping['TÍTULO']]) if 'TÍTULO' in mapping and text(source.iloc[i][mapping['TÍTULO']]).strip() else f'Sem título — linha {i + 2}' for i in range(len(source))]
    result['ESTADO NA FONTE'] = source[state_column].map(text).values if state_column is not None else ''
    ages, warnings, old = [], [], []
    for i in range(len(source)):
        parsed, warning = parse_request_date(source.iloc[i][date_column]) if date_column is not None else (None, 'Coluna de data não selecionada')
        age = (today - parsed).days if parsed else None
        if age is not None and age < 0:
            age, warning = None, 'Data futura por confirmar'
        ages.append(age)
        warnings.append(warning)
        old.append('Sim' if age is not None and age >= old_days else ('Não' if age is not None else 'Por confirmar'))
    result['DIAS EM ESPERA'] = pd.array(ages, dtype='Int64')
    result['PEDIDO ANTIGO'] = old
    result['AVISO DATA'] = warnings
    result['CAMPOS POR COMPLETAR / CONFIRMAR'] = [', '.join(f for f in FIELDS if f not in mapping or not text(source.iloc[i][mapping[f]]).strip()) for i in range(len(source))]
    result['_priority'] = result['PRIORIDADE LOCAL'].map({'Urgente': 0, 'Alta': 1, 'Normal': 2, 'Baixa': 3}).fillna(4)
    return result.sort_values(['_priority', 'DIAS EM ESPERA', 'LINHA EXCEL'], ascending=[True, False, True], na_position='last', kind='stable').drop(columns='_priority')


def export_workbook(source, notes, view):
    output = BytesIO()
    # Texto iniciado por '=' é texto, não uma fórmula executável na exportação.
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for name, frame in [('Recursos', source), ('Revisao_local', notes), ('Fila_semanal', view)]:
            frame.to_excel(writer, sheet_name=name, index=False)
            for row in writer.sheets[name].iter_rows():
                for cell in row:
                    if cell.data_type == 'f':
                        cell.data_type = 's'
    return output.getvalue()
