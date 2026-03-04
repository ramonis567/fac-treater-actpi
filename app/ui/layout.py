import streamlit as st
import pandas as pd
from io import BytesIO

from app.config.settings import APP_TITLE
from app.logic.processor import process_fac_and_eap


def render_app():
    st.set_page_config(
        page_title=APP_TITLE,
        layout="centered"
    )

    st.title(APP_TITLE)

    st.write(
        "Faça o upload da RD do projeto e selecione as abas de FAC e EAP."
    )

    # =========================================================
    # STATE MANAGEMENT
    # =========================================================
    if "merged_output" not in st.session_state:
        st.session_state.merged_output = None

    # =================================================
    # FILE UPLOADER
    # =================================================
    uploaded_file = st.file_uploader(
        "Faça o upload da RD",
        type=["xlsm", "xlsx", "xls"]
    )

    # Validação e processamento do arquivo
    if uploaded_file:
        try:
            excel_file = pd.ExcelFile(uploaded_file, engine="openpyxl")
            sheet_names = excel_file.sheet_names

            fac_sheet = st.selectbox(
                "Selecione a aba de FAC",
                sheet_names,
                index=sheet_names.index("FAC") if "FAC" in sheet_names else 0
            )

            eap_sheet = st.selectbox(
                "Selecione a aba de EAP",
                sheet_names,
                index=sheet_names.index("EAP") if "EAP" in sheet_names else 0
            )

            # =================================================
            # PROCESSAMENTO
            # =================================================
            if st.button("Executar Processamento"):
                with st.spinner("Processando FAC, EAP e Consolidação..."):

                    df_fac = excel_file.parse(sheet_name=fac_sheet)
                    df_eap = excel_file.parse(sheet_name=eap_sheet)

                    _, _, merged_processed = process_fac_and_eap(
                        df_fac, df_eap
                    )

                    # =============================================
                    # STORE CONSOLIDADO
                    # =============================================
                    merged_output = BytesIO()
                    with pd.ExcelWriter(merged_output, engine="openpyxl") as writer:
                        merged_processed.to_excel(
                            writer,
                            index=False,
                            sheet_name="FAC_EAP_CONSOLIDADO"
                        )
                    merged_output.seek(0)

                    st.session_state.merged_output = merged_output

                    st.success("Processamento concluído com sucesso.")

            # =================================================
            # DOWNLOAD FINAL
            # =================================================
            if st.session_state.merged_output is not None:
                st.download_button(
                    label="📥 Download FAC + EAP Consolidado",
                    data=st.session_state.merged_output,
                    file_name="FAC_EAP_CONSOLIDADO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
