
import streamlit as st
import pandas as pd

st.set_page_config(page_title="REDA - Catálogo de Recursos", layout="wide")

st.title("📚 Sistema de Catalogação REDA - Educação Física Açores")
st.write("Versão local com interface gráfica")

# Ajuda disponível antes do carregamento e durante a edição dos recursos.
st.header("Perguntas frequentes / Frequently asked questions")
with st.expander("Que ficheiro posso carregar? / What file can I upload?"):
    st.write("Carrega um ficheiro Excel .xlsx. A folha lida deve conter as colunas TÍTULO, AUTOR/FONTE, ORGANIZAÇÃO, DURAÇÃO DO VÍDEO e CÓDIGO DE INCORPORAÇÃO, com estes nomes exatos.")
    st.write("Upload an Excel .xlsx file. The worksheet being read must contain columns named exactly TÍTULO, AUTOR/FONTE, ORGANIZAÇÃO, DURAÇÃO DO VÍDEO and CÓDIGO DE INCORPORAÇÃO.")
with st.expander("Que campos posso editar? / Which fields can I edit?"):
    st.write("Depois de carregares o ficheiro, abre o painel de cada recurso. Podes editar Autor/Fonte, Organização, Duração do vídeo e Código de incorporação. O título é usado para identificar o recurso.")
    st.write("After uploading the file, open each resource panel. You can edit Autor/Fonte (Author/Source), Organização (Organization), Duração do vídeo (Video duration) and Código de incorporação (Embed code). The title identifies the resource.")
with st.expander("Como guardo as alterações? / How do I save my changes?"):
    st.write("Clica em Exportar Ficheiro Final e depois em Descarregar Excel Final. Guarda o ficheiro REDA_Recursos_Final.xlsx no teu dispositivo. O ficheiro original não é substituído por este botão.")
    st.write("Click “Exportar Ficheiro Final” (Export final file), then “Descarregar Excel Final” (Download final Excel). Save REDA_Recursos_Final.xlsx to your device. This button does not overwrite the original file.")
with st.expander("O que faço se o carregamento falhar? / What should I do if the upload fails?"):
    st.write("Confirma que o ficheiro é um Excel .xlsx válido e que a folha lida tem todas as colunas indicadas acima. Corrige o ficheiro e volta a carregá-lo. Guarda uma cópia do original antes de fazer alterações.")
    st.write("Check that the file is a valid Excel .xlsx workbook and that the worksheet being read contains all the columns listed above. Correct the file and upload it again. Keep a copy of the original before making changes.")
with st.expander("Esta ajuda aplica-se à app Apple? / Does this help apply to the Apple app?"):
    st.write("Esta ajuda descreve apenas esta interface Streamlit de catalogação REDA. Não descreve funcionalidades de uma versão Apple.")
    st.write("This help describes only this REDA Streamlit cataloguing interface. It does not describe features of an Apple version.")

# Upload do ficheiro de recursos
uploaded_file = st.file_uploader("Carrega o ficheiro Excel de Recursos", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.success("Ficheiro carregado com sucesso!")
    st.write("Pré-visualização dos dados:")
    st.dataframe(df)

    # Permitir edição dos campos que precisam ser validados
    st.write("Preencher/editar campos em falta:")

    for i in range(len(df)):
        with st.expander(f"Recurso {i+1}: {df.loc[i, 'TÍTULO']}"):
            df.at[i, 'AUTOR/FONTE'] = st.text_input("Autor/Fonte", value=df.loc[i, 'AUTOR/FONTE'], key=f"autor_{i}")
            df.at[i, 'ORGANIZAÇÃO'] = st.text_input("Organização", value=df.loc[i, 'ORGANIZAÇÃO'], key=f"org_{i}")
            df.at[i, 'DURAÇÃO DO VÍDEO'] = st.text_input("Duração do vídeo", value=df.loc[i, 'DURAÇÃO DO VÍDEO'], key=f"duracao_{i}")
            df.at[i, 'CÓDIGO DE INCORPORAÇÃO'] = st.text_input("Código de incorporação", value=df.loc[i, 'CÓDIGO DE INCORPORAÇÃO'], key=f"inc_{i}")

    # Botão para exportar ficheiro final
    if st.button("Exportar Ficheiro Final"):
        from io import BytesIO
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        st.download_button(
            label="Descarregar Excel Final",
            data=output.getvalue(),
            file_name="REDA_Recursos_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

