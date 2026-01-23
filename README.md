# Processador FAC + EAP (Actemium PI)

Este repositório contém uma **aplicação Streamlit** desenvolvida para processar, normalizar e consolidar planilhas de **FAC (Folha de Análise de Custos)** e **EAP (Estrutura Analítica do Projeto)** utilizadas em projetos da Actemium Power Industry.

A ferramenta extrai dados base das planilhas FAC, alinha essas informações à hierarquia da EAP e gera um **único arquivo Excel consolidado**, pronto para disponibilização técnica, relatórios e controle de produção.

Entende-se que a aplicação desta ferramenta é alinhada aos formatos de base próprios da unidade.

A ferramenta, em produção, pode ser acessada pelo link: https://fac-treater-actpi-bpwscatzgn8ddtdcrg9yuf.streamlit.app

---

## 🎯 Objetivo

Este aplicativo:

- Normaliza FAC e EAP dos arquivos base dos projetos;
- Gera um **Excel limpo e estruturado** para disponibilização.

---

## 🧠 Conceitos-Chave

### Tratamento da Hierarquia da EAP

| Nível | Padrão        | Significado            |
|------:|---------------|------------------------|
| 2     | `X.X`         | **SUBESTAÇÃO**         |
| 3     | `X.X.X`       | **TAG (nível lógico)** |
| 4     | `X.X.X.X`     | **Item executável**    |

A consolidação ocorre **exclusivamente no nível 4**.  
Os níveis 2 e 3 são utilizados para contextualização.

---

### Lógica de TAG

As TAGs são extraídas da **descrição do nível 3** e divididas em:

- `TAG_CODE` → identificador curto (ex.: `UAC1`);
- `TAG_DESCRICAO` → descrição completa.

Quando uma TAG possui múltiplos códigos  
(ex.: `UAC1 / UAC2 / UAC3`), a linha é **explodida**, replicando os valores de esforço para cada TAG individual.

---

## 📂 Estrutura de Diretórios
fac-treater-actpi/
├── README.md
├── main.py
├── requirements.txt
└── app/
├── config/
│ └── settings.py
├── logic/
│ ├── eap_processor.py
│ └── processor.py
└── ui/
└── layout.py

---

## ⚙️ Pipeline de Processamento

### 1. Processamento da FAC
- Detecção dinâmica da linha real de cabeçalho;
- Normalização das colunas numéricas de esforço;
- Mantém apenas:
  - `DESCRIÇÃO`;
  - Colunas de esforço (MAT, ENG, FAB, MONT, etc.);
- Remove custos e linhas irrelevantes.

### 2. Processamento da EAP
- Identifica `ITEM` e `DESCRICAO`;
- Detecta colunas numéricas automaticamente;
- Infere `QTDE` e `TOTAL`;
- Mantém apenas itens válidos com valor.

### 3. Consolidação
- Filtra apenas itens **nível X.X.X.X**;
- Adiciona:
  - `SUBESTACAO` (descrição do nível X.X);
  - `TAG_CODE` e `TAG_DESCRICAO` (nível X.X.X);
- Consolida dados da FAC pela descrição;
- Remove todas as colunas de `QTDE` no resultado final.

### 4. Explosão de TAG
- Divide linhas com múltiplos códigos de TAG;
- Mantém os mesmos valores de esforço em cada linha.

---

## 📤 Saída Gerada

O sistema gera **um único arquivo Excel final**:

- **Aba:** `FAC_EAP_CONSOLIDADO`
- **Principais colunas:**
  - `ITEM`
  - `SUBESTACAO`
  - `TAG_CODE`
  - `TAG_DESCRICAO`
  - `DESCRICAO`
  - Colunas de esforço (MAT, ENG, FAB, MONT…)

Arquivos intermediários (FAC_TRATADO, EAP_TRATADO) **não são expostos na interface**, evitando uso indevido.

---

## 🖥️ Interface do Usuário

A interface foi mantida propositalmente simples:

1. Upload do arquivo Excel da RD;
2. Seleção das abas:
   - FAC;
   - EAP;
3. Execução do processamento;
4. Download do arquivo consolidado.

Nenhuma configuração adicional é necessária.

---

## ▶️ Como Executar (Ambiente de Desenvolvimento)

### ✅ Pré-requisitos

- **Python 3.10 ou 3.11**  
  > Recomendado: Python 3.11  
  (compatível com pandas, openpyxl e Streamlit utilizados no projeto)

- **Git** instalado
- Sistema operacional:
  - Windows (CMD ou PowerShell)
  - Linux ou macOS (terminal padrão)

---

### 1️⃣ Clonar o repositório

Abra o terminal (CMD, PowerShell ou bash) e execute:

```bash
git clone https://github.com/ramonis567/ramonis567-fac-treater-actpi.git
```

Entre no diretório do projeto:
```bash
cd ramonis567-fac-treater-actpi
```

### 2️⃣ Clonar o repositório
Criar ambiente virtual (recomendado)
Windows – PowerShell
```PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Caso o PowerShell bloqueie scripts, execute uma vez:
```PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Windows – CMD
```CMD
python -m venv .venv
.venv\Scripts\activate.bat
```

Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Instalar dependências

Com o ambiente virtual ativado:
```bash
pip install -r requirements.txt
```

Se houver problemas de versão do pip:
```bash
python -m pip install --upgrade pip
```

### 4️⃣ Executar a aplicação
Via Streamlit (modo desenvolvimento)
```bash
streamlit run main.py
```

Após a execução, o terminal exibirá algo como:
```bash
Local URL: http://localhost:8501
```

Abra o endereço no navegador.

### 5️⃣ Uso no navegador

- Faça upload do arquivo Excel da RD;
- Selecione as abas:
    -  FAC
    -  EAP

- Clique em Executar Processamento;
- Faça o download do arquivo 
    - FAC_EAP_CONSOLIDADO.xlsx.

---

## 🧪 Observações Importantes

- O aplicativo **não grava arquivos no disco** — todo o processamento ocorre em memória;
- O processamento é **síncrono**, adequado para uso interno;
- As abas **FAC** e **EAP** devem estar no **mesmo arquivo Excel**, em abas distintas;
- A detecção de colunas é dinâmica, porém:
  - A **EAP** deve conter níveis hierárquicos no formato `X.X`, `X.X.X` e `X.X.X.X`;
  - A **FAC** deve conter uma coluna **DESCRIÇÃO** válida.


## 🔧 Dicas de Debug

Para ativar logs detalhados, edite no arquivo **app/logic/processor.py***:

```python
DEBUG = True
```

Com isso, todas as etapas do pipeline serão exibidas no terminal durante a execução.