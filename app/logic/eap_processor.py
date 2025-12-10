import pandas as pd


def process_eap_data(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("A aba EAP está vazia.")

    df = df.copy()
    df = df.dropna(how="all").reset_index(drop=True)

    if df.shape[1] < 5:
        raise ValueError("Formato inválido da EAP. Planilha com poucas colunas.")

    # ============================
    # 1) MAPEIA AS DUAS PRIMEIRAS COLUNAS FIXAS
    # ============================
    df.rename(columns={df.columns[0]: "ITEM", df.columns[1]: "DESCRICAO"}, inplace=True)

    # ============================
    # 2) CONVERTE TODAS AS OUTRAS COLUNAS PARA NÚMEROS
    # ============================
    numeric_candidates = []

    for col in df.columns[2:]:
        temp = (
            df[col]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        temp = pd.to_numeric(temp, errors="coerce")

        df[col] = temp

        # Marca colunas que realmente têm números válidos
        if temp.notna().sum() > 5:
            numeric_candidates.append(col)

    if not numeric_candidates:
        raise ValueError("Nenhuma coluna numérica foi detectada na EAP.")

    # ============================
    # 3) DEFINE QTDE E TOTAL DE FORMA INTELIGENTE
    # ============================
    qtde_col = numeric_candidates[0]
    total_col = numeric_candidates[-1]

    df.rename(columns={
        qtde_col: "QTDE",
        total_col: "TOTAL"
    }, inplace=True)

    # ============================
    # 4) LIMPEZA E FILTRO FINAL
    # ============================
    df = df[["ITEM", "DESCRICAO", "QTDE", "TOTAL"]]

    df = df[
        (df["QTDE"].notna()) &
        (df["QTDE"] > 0) &
        (df["TOTAL"].notna()) &
        (df["TOTAL"] > 0)
    ]

    # Remove cabeçalhos, propostas, clientes e seções
    df = df[~df["ITEM"].astype(str).str.contains(
        "Proposta|Cliente|SUBESTA|TOTAL|EAP|nan",
        case=False,
        na=False
    )]

    df["DESCRICAO"] = df["DESCRICAO"].astype(str).str.strip()

    df = df.reset_index(drop=True)

    if df.empty:
        raise ValueError(
            "Nenhuma linha válida foi gerada a partir da EAP.\n"
            "Verifique se existem valores numéricos reais na coluna TOTAL."
        )

    return df
