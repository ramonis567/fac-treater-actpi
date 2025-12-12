import pandas as pd
import re

from app.logic.eap_processor import process_eap_data

DEBUG = True  # 🔁 Coloque False em produção


def _debug(msg: str):
    if DEBUG:
        print(f"[DEBUG] {msg}")


# ============================================================
#  VALIDATION
# ============================================================

def validate_input(df: pd.DataFrame) -> None:
    if df is None:
        raise ValueError("Nenhum dado foi recebido para processamento.")

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Entrada inválida: o dado recebido não é um DataFrame.")

    if df.empty:
        raise ValueError("A planilha está vazia.")

    if len(df.columns) == 0:
        raise ValueError("A planilha não contém colunas.")

    _debug(f"Planilha validada: {df.shape[0]} linhas, {df.shape[1]} colunas.")


# ============================================================
#  FAC – PREPROCESS
# ============================================================

def preprocess_fac(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all").reset_index(drop=True)

    _debug(f"[FAC] Após limpeza inicial: {df.shape[0]} linhas restantes.")
    return df


# ============================================================
#  FAC – BUSINESS LOGIC (SEM CUSTOS)
# ============================================================

def apply_business_logic_fac(df: pd.DataFrame) -> pd.DataFrame:

    # 1) Localiza linha do cabeçalho
    header_row_idx = None
    for i in range(len(df)):
        row_values = df.iloc[i].astype(str).str.strip().str.upper().values
        if "DESCRIÇÃO" in row_values:
            header_row_idx = i
            break

    if header_row_idx is None:
        raise ValueError("Não foi possível localizar a linha de cabeçalho com 'DESCRIÇÃO' na FAC.")

    _debug(f"[FAC] Cabeçalho localizado na linha {header_row_idx}")

    # 2) Promove cabeçalho
    df = df.iloc[header_row_idx:].copy().reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df.iloc[1:].copy().reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip()

    _debug(f"[FAC] Colunas detectadas: {list(df.columns)}")

    preco_col = "PREÇO DE_x000D_\nVENDA (UNIT)"
    if preco_col in df.columns:
        df = df.dropna(subset=[preco_col])

    if "DESCRIÇÃO" not in df.columns:
        raise ValueError("[FAC] Coluna 'DESCRIÇÃO' não encontrada após promoção do cabeçalho.")

    descricao_col = "DESCRIÇÃO"

    funcoes_desejadas = [
        "QTDE",
        "MAT. ESPEC.",
        "MAT. GERAL",
        "COOR ENG DTFD",
        "CONS ENG DTFD",
        "PROJ DTFD",
        "APOIO DTFD",
        "FAB MEC",
        "MONT MEC",
        "MONT ELET",
    ]

    # Detecta colunas existentes
    funcoes_detectadas = []
    upper_map = {c.upper(): c for c in df.columns}
    for f in funcoes_desejadas:
        if f.upper() in upper_map:
            funcoes_detectadas.append(upper_map[f.upper()])

    if not funcoes_detectadas:
        raise ValueError("[FAC] Nenhuma coluna de função válida foi detectada na FAC.")

    _debug(f"[FAC] Funções utilizadas como colunas: {funcoes_detectadas}")

    # Normaliza números
    for funcao in funcoes_detectadas:
        df[funcao] = df[funcao].astype(str).str.replace(",", ".", regex=False).str.strip()
        df[funcao] = pd.to_numeric(df[funcao], errors="coerce").fillna(0)

    output_df = df[[descricao_col] + funcoes_detectadas].copy()
    output_df = output_df[output_df[descricao_col].notna()].reset_index(drop=True)

    return output_df


def postprocess_fac(df: pd.DataFrame) -> pd.DataFrame:
    return df.reset_index(drop=True)


def process_fac(df: pd.DataFrame) -> pd.DataFrame:
    validate_input(df)
    df = preprocess_fac(df)
    df = apply_business_logic_fac(df)
    df = postprocess_fac(df)
    return df


# ============================================================
#  TAG SPLIT FUNCTION
# ============================================================

def split_tag(tag: str):
    """Divide TAG em TAG_CODE e TAG_DESCRICAO."""
    if not tag or str(tag).lower() == "nan":
        return "", ""

    parts = re.split(r"\s*-\s*", tag, maxsplit=1)

    if len(parts) == 1:
        return parts[0].strip(), ""

    return parts[0].strip(), parts[1].strip()


# ============================================================
#  MERGE FAC + EAP + SUBESTACAO + TAG
# ============================================================

def merge_fac_eap(fac_df: pd.DataFrame, eap_df: pd.DataFrame) -> pd.DataFrame:
    fac = fac_df.copy()
    eap = eap_df.copy()

    fac.columns = fac.columns.astype(str).str.strip()
    eap.columns = eap.columns.astype(str).str.strip()

    if "DESCRIÇÃO" not in fac.columns:
        raise ValueError("FAC não possui coluna 'DESCRIÇÃO'.")
    if "DESCRICAO" not in eap.columns:
        raise ValueError("EAP não possui coluna 'DESCRICAO'.")
    if "ITEM" not in eap.columns:
        raise ValueError("EAP não possui coluna 'ITEM'.")

    # --------------------------------------------------------
    # LEVEL 2 → X.X  (vira SUBESTACAO)
    # --------------------------------------------------------
    regex_lvl2 = r"^\d+\.\d+$"
    eap_lvl2 = eap[eap["ITEM"].astype(str).str.match(regex_lvl2, na=False)]
    level2_map = dict(zip(eap_lvl2["ITEM"], eap_lvl2["DESCRICAO"]))

    def find_subestacao(item: str) -> str:
        key = ".".join(item.split(".")[:2])
        return level2_map.get(key, "")

    # --------------------------------------------------------
    # LEVEL 3 → TAG
    # --------------------------------------------------------
    regex_lvl3 = r"^\d+\.\d+\.\d+$"
    eap_lvl3 = eap[eap["ITEM"].astype(str).str.match(regex_lvl3, na=False)]
    level3_map = dict(zip(eap_lvl3["ITEM"], eap_lvl3["DESCRICAO"]))

    def find_parent_tag(item: str) -> str:
        parts = item.split(".")
        if len(parts) == 4:
            parent = ".".join(parts[:3])
            return level3_map.get(parent, "")
        return ""

    # --------------------------------------------------------
    # LEVEL 4 rows only
    # --------------------------------------------------------
    regex_lvl4 = r"^\d+\.\d+\.\d+\.\d+$"
    eap_lvl4 = eap[eap["ITEM"].astype(str).str.match(regex_lvl4, na=False)].copy()

    # SUBESTACAO COLUMN (antes era LEVEL_2)
    eap_lvl4["SUBESTACAO"] = eap_lvl4["ITEM"].astype(str).apply(find_subestacao)

    # TAG RAW (temporário; será removido ao final do pipeline)
    eap_lvl4["TAG_RAW"] = eap_lvl4["ITEM"].astype(str).apply(find_parent_tag)

    # TAG_CODE + TAG_DESCRICAO
    eap_lvl4[["TAG_CODE", "TAG_DESCRICAO"]] = eap_lvl4["TAG_RAW"].apply(
        lambda x: pd.Series(split_tag(x))
    )

    # --------------------------------------------------------
    # MERGE FAC
    # --------------------------------------------------------
    fac_functions = [c for c in fac.columns if c != "DESCRIÇÃO"]

    merged = eap_lvl4.merge(
        fac,
        how="left",
        left_on="DESCRICAO",
        right_on="DESCRIÇÃO"
    )

    if "DESCRIÇÃO" in merged.columns:
        merged = merged.drop(columns=["DESCRIÇÃO"])

    for col in fac_functions:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    # Remove QTDE columns
    qtde_cols = [c for c in merged.columns if c.upper().startswith("QTDE")]
    merged = merged.drop(columns=qtde_cols, errors="ignore")

    # Order columns: ITEM | SUBESTACAO | TAG_CODE | TAG_DESCRICAO | TAG_RAW | ...
    priority_cols = ["ITEM", "SUBESTACAO", "TAG_CODE", "TAG_DESCRICAO", "TAG_RAW"]
    other_cols = [c for c in merged.columns if c not in priority_cols]
    merged = merged[priority_cols + other_cols]

    return merged.reset_index(drop=True)


# ============================================================
#  EXPLODE TAG
# ============================================================

def explode_by_tag(df: pd.DataFrame) -> pd.DataFrame:

    if "TAG_CODE" not in df.columns:
        return df

    rows = []

    for _, row in df.iterrows():
        codes = [c.strip() for c in str(row["TAG_CODE"]).split("/") if c.strip()]
        desc = row.get("TAG_DESCRICAO", "")

        if len(codes) <= 1:
            rows.append(row)
            continue

        for code in codes:
            new_row = row.copy()
            new_row["TAG_CODE"] = code
            # TAG_RAW existe só para auditoria; explode mantém coerência
            new_row["TAG_RAW"] = f"{code} - {desc}" if desc else code
            rows.append(new_row)

    return pd.DataFrame(rows).reset_index(drop=True)


# ============================================================
#  PIPELINE COMPLETO
# ============================================================

def process_fac_and_eap(fac_df: pd.DataFrame, eap_df: pd.DataFrame):

    _debug("=== Processando FAC ===")
    fac_processed = process_fac(fac_df)

    _debug("=== Processando EAP ===")
    eap_processed = process_eap_data(eap_df)

    _debug("=== Merge FAC + EAP ===")
    merged = merge_fac_eap(fac_processed, eap_processed)

    _debug("=== Explodindo TAGs ===")
    merged_exploded = explode_by_tag(merged)

    # ✅ REMOVE TAG_RAW SOMENTE NO FINAL
    if "TAG_RAW" in merged_exploded.columns:
        merged_exploded = merged_exploded.drop(columns=["TAG_RAW"])

    # ✅ GARANTE SUBESTACAO NA 2ª COLUNA
    if "SUBESTACAO" in merged_exploded.columns and "ITEM" in merged_exploded.columns:
        col_order = ["ITEM", "SUBESTACAO"] + [c for c in merged_exploded.columns if c not in ("ITEM", "SUBESTACAO")]
        merged_exploded = merged_exploded[col_order]

    return fac_processed, eap_processed, merged_exploded
