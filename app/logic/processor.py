import pandas as pd
import re

from app.logic.eap_processor import process_eap_data

DEBUG = True  # 🔁 Set False in production


def _debug(msg: str):
    if DEBUG:
        print(f"[DEBUG] {msg}")


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def validate_input(df: pd.DataFrame, name: str = "DataFrame") -> None:
    if df is None:
        raise ValueError(f"{name} não recebido.")

    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{name} não é um DataFrame válido.")

    if df.empty:
        raise ValueError(f"{name} está vazio.")

    if len(df.columns) == 0:
        raise ValueError(f"{name} não contém colunas.")

    _debug(f"{name} validado: {df.shape[0]} linhas, {df.shape[1]} colunas.")


# ─────────────────────────────────────────────
# PREPROCESS GENÉRICO
# ─────────────────────────────────────────────

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all").reset_index(drop=True)
    return df


# ─────────────────────────────────────────────
# TRATAMENTO FAC
# ─────────────────────────────────────────────

def process_fac_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Saída final FAC:
    DESCRIÇÃO | QTDE | MAT. ESPEC. | MAT. GERAL | COOR ENG DTFD | ...
    """

    validate_input(df, "FAC")
    df = preprocess(df)

    # 1️⃣ Localiza linha do cabeçalho real (onde aparece 'DESCRIÇÃO')
    header_row_idx = None
    for i in range(len(df)):
        row_values = df.iloc[i].astype(str).str.strip().str.upper().values
        if "DESCRIÇÃO" in row_values:
            header_row_idx = i
            break

    if header_row_idx is None:
        raise ValueError("FAC: Não foi possível localizar a linha de cabeçalho com 'DESCRIÇÃO'.")

    _debug(f"FAC: Cabeçalho localizado na linha {header_row_idx}")

    # 2️⃣ Promove o cabeçalho
    df = df.iloc[header_row_idx:].copy().reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df.iloc[1:].copy().reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip()

    _debug(f"FAC: Colunas detectadas após promoção: {list(df.columns)}")

    if "DESCRIÇÃO" not in df.columns:
        raise ValueError("FAC: Coluna 'DESCRIÇÃO' não encontrada após promoção do cabeçalho.")

    # 3️⃣ Define funções desejadas (lista branca)
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

    # Mantém apenas as que realmente existem
    funcoes_detectadas = []
    alvo_upper = [f.upper() for f in funcoes_desejadas]

    for col in df.columns:
        if col.upper() in alvo_upper:
            funcoes_detectadas.append(col)

    if not funcoes_detectadas:
        raise ValueError("FAC: Nenhuma coluna de função válida detectada.")

    _debug(f"FAC: Funções utilizadas como colunas: {funcoes_detectadas}")

    # 4️⃣ Normaliza valores numéricos
    for col in funcoes_detectadas:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 5️⃣ Saída final FAC
    output_df = df[["DESCRIÇÃO"] + funcoes_detectadas].copy()
    output_df = output_df[output_df["DESCRIÇÃO"].notna()].reset_index(drop=True)

    _debug(f"FAC processado com shape: {output_df.shape}")

    return output_df


# ─────────────────────────────────────────────
# MERGE FAC + EAP
# ─────────────────────────────────────────────

def merge_fac_eap(fac_df: pd.DataFrame, eap_df: pd.DataFrame) -> pd.DataFrame:
    """
    Regras de merge:
    - Tabela base: EAP
    - Match APENAS POR DESCRIÇÃO, conforme alinhado
    - Nível de interesse em EAP: somente itens ITEM no formato X.X.X.X
    - LEFT JOIN: EAP sempre preserva linhas
    - Colunas do FAC preenchidas com 0 quando não houver match
    - TOTAL da EAP preservado
    """

    fac_df = fac_df.copy()
    eap_df = eap_df.copy()

    # Normaliza nomes de colunas
    fac_df.columns = fac_df.columns.astype(str).str.strip()
    eap_df.columns = eap_df.columns.astype(str).str.strip()

    # Garantir colunas mínimas
    if "DESCRIÇÃO" not in fac_df.columns:
        raise ValueError("FAC não possui coluna 'DESCRIÇÃO'.")

    if "DESCRICAO" not in eap_df.columns:
        raise ValueError("EAP não possui coluna 'DESCRICAO'.")

    if "ITEM" not in eap_df.columns:
        raise ValueError("EAP não possui coluna 'ITEM' para identificar nível.")

    # 1️⃣ Filtra EAP somente para nível X.X.X.X
    nivel_regex = r"^\d+\.\d+\.\d+\.\d+$"
    eap_nivel = eap_df[
        eap_df["ITEM"].astype(str).str.match(nivel_regex, na=False)
    ].copy()

    _debug(f"EAP: Linhas no nível X.X.X.X: {eap_nivel.shape[0]}")

    # 2️⃣ Colunas de função do FAC (tudo que não for 'DESCRIÇÃO')
    fac_function_cols = [c for c in fac_df.columns if c != "DESCRIÇÃO"]

    _debug(f"Merge: Colunas de função do FAC: {fac_function_cols}")

    # 3️⃣ Merge LEFT: EAP base, join por descrição
    merged = eap_nivel.merge(
        fac_df,
        how="left",
        left_on="DESCRICAO",
        right_on="DESCRIÇÃO"
    )

    # 4️⃣ Zera funções FAC onde não houve match
    for col in fac_function_cols:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    # 5️⃣ Remove coluna de chave duplicada se quiser
    # (mantemos DESCRICAO da EAP, e opcionalmente removemos DESCRIÇÃO do FAC)
    if "DESCRIÇÃO" in merged.columns:
        merged = merged.drop(columns=["DESCRIÇÃO"])

    merged = merged.reset_index(drop=True)

    _debug(f"Merge FAC + EAP concluído: {merged.shape}")

    return merged


# ─────────────────────────────────────────────
# PIPELINE GLOBAL
# ─────────────────────────────────────────────

def process_fac_and_eap(fac_df: pd.DataFrame, eap_df: pd.DataFrame):
    """
    Pipeline principal:
    1) Processa FAC
    2) Processa EAP (via eap_processor)
    3) Consolida FAC → EAP
    """

    fac_processed = process_fac_data(fac_df)
    eap_processed = process_eap_data(eap_df)

    merged_df = merge_fac_eap(fac_processed, eap_processed)

    return fac_processed, eap_processed, merged_df
