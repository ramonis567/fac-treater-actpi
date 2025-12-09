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
    Tratamento final (sem custos):
    - Localiza dinamicamente a linha real de cabeçalho (onde existe 'DESCRIÇÃO')
    - Promove essa linha como cabeçalho
    - Normaliza para:
      DESCRIÇÃO | FUNÇÃO | HORAS
    """

    # ─────────────────────────────────────────────
    # 1️⃣ LOCALIZA A LINHA REAL DE CABEÇALHO
    # ─────────────────────────────────────────────

    header_row_idx = None

    for i in range(len(df)):
        row_values = df.iloc[i].astype(str).str.strip().str.upper().values
        if "DESCRIÇÃO" in row_values:
            header_row_idx = i
            break

    if header_row_idx is None:
        raise ValueError(
            "Não foi possível localizar a linha de cabeçalho com a coluna 'DESCRIÇÃO'."
        )

    _debug(f"Linha real de cabeçalho localizada no índice {header_row_idx}")

    # ─────────────────────────────────────────────
    # 2️⃣ PROMOVE O CABEÇALHO REAL
    # ─────────────────────────────────────────────

    df = df.iloc[header_row_idx:].copy().reset_index(drop=True)

    df.columns = df.iloc[0]
    df = df.iloc[1:].copy().reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip()

    _debug(f"Cabeçalhos finais: {list(df.columns)}")

    # ─────────────────────────────────────────────
    # 3️⃣ VALIDA COLUNA DE DESCRIÇÃO
    # ─────────────────────────────────────────────

    if "DESCRIÇÃO" not in df.columns:
        raise ValueError(
            f"Coluna 'DESCRIÇÃO' não encontrada. Colunas disponíveis: {list(df.columns)}"
        )

    descricao_col = "DESCRIÇÃO"

    # ─────────────────────────────────────────────
    # 4️⃣ FILTRA COLUNAS DE FUNÇÃO
    # ─────────────────────────────────────────────

    funcoes_validas = []

    for col in df.columns:
        col_str = str(col).upper()

        if col_str in ["ITEM", "DESCRIÇÃO"]:
            continue
        if "%" in col_str:
            continue
        if "VALOR" in col_str:
            continue
        if "PREÇO" in col_str:
            continue
        if "SOMA" in col_str:
            continue
        if "DATA BASE" in col_str:
            continue

        funcoes_validas.append(col)

    if not funcoes_validas:
        raise ValueError("Nenhuma coluna de função válida foi detectada.")

    _debug(f"Funções válidas detectadas: {funcoes_validas}")

    # ─────────────────────────────────────────────
    # 5️⃣ NORMALIZA PARA FORMATO FINAL
    # ─────────────────────────────────────────────

    output_rows = []

    for _, row in df.iterrows():
        descricao = row.get(descricao_col)

        if pd.isna(descricao):
            continue

        for funcao in funcoes_validas:
            horas = row.get(funcao)

            if pd.isna(horas):
                continue

            try:
                horas = float(str(horas).replace(",", "."))
            except (ValueError, TypeError):
                continue

            if horas == 0:
                continue

            output_rows.append({
                "DESCRIÇÃO": descricao,
                "FUNÇÃO": funcao,
                "HORAS": horas
            })

    if not output_rows:
        raise ValueError(
            "Nenhuma linha válida foi gerada. "
            "Verifique se existem valores numéricos de horas nas colunas de função."
        )

    output_df = pd.DataFrame(output_rows)

    _debug(f"{len(output_df)} linhas normalizadas geradas.")

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
