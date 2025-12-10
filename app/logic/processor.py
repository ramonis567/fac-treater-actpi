import pandas as pd

DEBUG = True  # 🔁 Set False in production


def _debug(msg: str):
    if DEBUG:
        print(f"[DEBUG] {msg}")


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# PREPROCESS
# ─────────────────────────────────────────────

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpeza inicial dos dados.
    """
    df = df.copy()

    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all").reset_index(drop=True)

    _debug(f"Após limpeza inicial: {df.shape[0]} linhas restantes.")
    return df


# ─────────────────────────────────────────────
# BUSINESS LOGIC (SEM CUSTOS)
# ─────────────────────────────────────────────

def apply_business_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nova versão:
    - Localiza dinamicamente a linha de cabeçalho real ('DESCRIÇÃO')
    - Normaliza dados
    - Transforma FUNÇÕES em COLUNAS (pivot)
    """

    # ─────────────────────────────────────────────
    # 1️⃣ LOCALIZA A LINHA REAL DO CABEÇALHO
    # ─────────────────────────────────────────────
    header_row_idx = None

    for i in range(len(df)):
        row_values = df.iloc[i].astype(str).str.strip().str.upper().values
        if "DESCRIÇÃO" in row_values:
            header_row_idx = i
            break

    if header_row_idx is None:
        raise ValueError("Não foi possível localizar a linha de cabeçalho com 'DESCRIÇÃO'.")

    _debug(f"Cabeçalho localizado na linha {header_row_idx}")

    # ─────────────────────────────────────────────
    # 2️⃣ PROMOVE CABEÇALHO
    # ─────────────────────────────────────────────
    df = df.iloc[header_row_idx:].copy().reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df.iloc[1:].copy().reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip()

    _debug(f"Colunas detectadas: {list(df.columns)}")

    df.dropna(subset=["PREÇO DE_x000D_\nVENDA (UNIT)"], inplace=True)
    print(df.head(10))

    # ─────────────────────────────────────────────
    # 3️⃣ IDENTIFICA COLUNA DESCRIÇÃO
    # ─────────────────────────────────────────────
    if "DESCRIÇÃO" not in df.columns:
        raise ValueError("Coluna 'DESCRIÇÃO' não encontrada após promoção do cabeçalho.")

    descricao_col = "DESCRIÇÃO"

    # ─────────────────────────────────────────────
    # 4️⃣ DEFINE FUNÇÕES COMO COLUNAS (LISTA BRANCA)
    # ─────────────────────────────────────────────
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

    # Mantém também qualquer outra função nova que venha futuramente
    funcoes_detectadas = []

    for col in df.columns:
        if col == descricao_col:
            continue
        if col.upper() in [c.upper() for c in funcoes_desejadas]:
            funcoes_detectadas.append(col)

    if not funcoes_detectadas:
        raise ValueError("Nenhuma coluna de função válida foi detectada.")

    _debug(f"Funções utilizadas como colunas: {funcoes_detectadas}")

    # ─────────────────────────────────────────────
    # 5️⃣ LIMPA E NORMALIZA OS VALORES NUMÉRICOS
    # ─────────────────────────────────────────────
    for funcao in funcoes_detectadas:
        df[funcao] = (
            df[funcao]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[funcao] = pd.to_numeric(df[funcao], errors="coerce").fillna(0)

    # ─────────────────────────────────────────────
    # 6️⃣ RETORNA NO FORMATO FINAL (DESCRIÇÃO + FUNÇÕES-COLUNAS)
    # ─────────────────────────────────────────────
    output_df = df[[descricao_col] + funcoes_detectadas].copy()

    output_df = output_df[output_df[descricao_col].notna()]
    output_df = output_df.reset_index(drop=True)

    _debug(f"Formato final gerado com {output_df.shape[0]} linhas e {output_df.shape[1]} colunas.")

    return output_df

# ─────────────────────────────────────────────
# POSTPROCESS
# ─────────────────────────────────────────────

def postprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    return df


# ─────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    validate_input(df)
    df = preprocess(df)
    df = apply_business_logic(df)
    df = postprocess(df)
    return df
