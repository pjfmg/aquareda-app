
import streamlit as st
import pandas as pd

st.set_page_config(page_title="REDA - Catálogo de Recursos", layout="wide")

st.title("📚 Sistema de Catalogação REDA - Educação Física Açores")
st.write("Versão local com interface gráfica")

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
