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

    # ✅ INIT SESSION STATE
    if "fac_output" not in st.session_state:
        st.session_state.fac_output = None

    if "eap_output" not in st.session_state:
        st.session_state.eap_output = None

    if "merged_output" not in st.session_state:
        st.session_state.merged_output = None

    uploaded_file = st.file_uploader(
        "Faça o upload da RD",
        type=["xlsm", "xlsx", "xls"]
    )

    if uploaded_file:
        try:
            excel_file = pd.ExcelFile(uploaded_file)
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

            st.info(f"FAC selecionado: {fac_sheet}")
            st.info(f"EAP selecionado: {eap_sheet}")

            if st.button("Executar Processamento"):
                with st.spinner("Processando FAC, EAP e Consolidação..."):

                    df_fac = pd.read_excel(
                        uploaded_file,
                        sheet_name=fac_sheet,
                        engine="openpyxl"
                    )

                    df_eap = pd.read_excel(
                        uploaded_file,
                        sheet_name=eap_sheet,
                        engine="openpyxl"
                    )

                    # ✅ AGORA RECEBE 3 RETORNOS
                    fac_processed, eap_processed, merged_processed = process_fac_and_eap(
                        df_fac, df_eap
                    )

                    # ==========================
                    # ✅ STORE FAC IN SESSION
                    # ==========================
                    fac_output = BytesIO()
                    with pd.ExcelWriter(fac_output, engine="openpyxl") as writer:
                        fac_processed.to_excel(
                            writer, index=False, sheet_name="FAC_TRATADO"
                        )
                    fac_output.seek(0)
                    st.session_state.fac_output = fac_output

                    # ==========================
                    # ✅ STORE EAP IN SESSION
                    # ==========================
                    eap_output = BytesIO()
                    with pd.ExcelWriter(eap_output, engine="openpyxl") as writer:
                        eap_processed.to_excel(
                            writer, index=False, sheet_name="EAP_TRATADO"
                        )
                    eap_output.seek(0)
                    st.session_state.eap_output = eap_output

                    # ==========================
                    # ✅ STORE CONSOLIDADO IN SESSION
                    # ==========================
                    merged_output = BytesIO()
                    with pd.ExcelWriter(merged_output, engine="openpyxl") as writer:
                        merged_processed.to_excel(
                            writer, index=False, sheet_name="FAC_EAP_CONSOLIDADO"
                        )
                    merged_output.seek(0)
                    st.session_state.merged_output = merged_output

                    st.success("FAC, EAP e Consolidação processados com sucesso.")

            # ==========================
            # ✅ ALWAYS SHOW DOWNLOADS IF EXISTS
            # ==========================
            if st.session_state.fac_output is not None:
                st.download_button(
                    label="📥 Download FAC Tratado",
                    data=st.session_state.fac_output,
                    file_name="FAC_TRATADO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            if st.session_state.eap_output is not None:
                st.download_button(
                    label="📥 Download EAP Tratado",
                    data=st.session_state.eap_output,
                    file_name="EAP_TRATADO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            if st.session_state.merged_output is not None:
                st.download_button(
                    label="📥 Download FAC + EAP Consolidado",
                    data=st.session_state.merged_output,
                    file_name="FAC_EAP_CONSOLIDADO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
