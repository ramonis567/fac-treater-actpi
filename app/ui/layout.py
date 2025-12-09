import streamlit as st
import pandas as pd
from io import BytesIO

from app.config.settings import APP_TITLE, OUTPUT_SHEET_NAME
from app.logic.processor import process_data


def render_app():
    st.set_page_config(
        page_title=APP_TITLE,
        layout="centered"
    )

    st.title(APP_TITLE)

    st.write(
        "Faça o upload da RD do projeto e selecione a respectiva tabela (aba) de FAC. Feito isto, clique para executar."
    )

    uploaded_file = st.file_uploader(
        "Faça o upload da RD",
        type=["xlsm", "xlsx"]
    )

    if uploaded_file:
        try:
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names

            selected_sheet = st.selectbox(
                "Selecione a aba de FAC para processar",
                sheet_names
            )

            if st.button("Executar Processamento"):
                with st.spinner("Processando tabela..."):
                    df = pd.read_excel(
                        uploaded_file,
                        sheet_name=selected_sheet,
                        engine="openpyxl"
                    )

                    processed_df = process_data(df)

                    output = BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        processed_df.to_excel(
                            writer,
                            index=False,
                            sheet_name=OUTPUT_SHEET_NAME
                        )

                    output.seek(0)

                    st.success("Processamento concluído com sucesso.")

                    st.download_button(
                        label="Faça o download",
                        data=output,
                        file_name=f"{selected_sheet}_processed.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        except Exception as e:
            st.error(f"Error reading file: {e}")
