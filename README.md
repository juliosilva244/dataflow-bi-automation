# 🚀 DataFlow BI Automation

Plataforma profissional de Business Intelligence em Python para transformar planilhas Excel/CSV em dashboards executivos, KPIs automáticos, análise de schema, insights e relatórios exportáveis.

---

## 📊 Visão geral

O **DataFlow BI Automation** analisa bases tabulares automaticamente, identifica a métrica principal, detecta dimensões relevantes, gera KPIs, cria gráficos interativos e permite exportação em Excel/PDF.

O projeto foi desenhado para portfólio profissional em Dados/BI, com foco em automação analítica, Streamlit, Pandas, Plotly e integração opcional com IA via Groq.

---

## ✨ Recursos

- Upload de arquivos `.xlsx`, `.xls` e `.csv`
- Base padrão de demonstração
- Detecção automática de schema
- Identificação de:
  - métrica principal
  - coluna de data
  - dimensão principal
  - dimensão secundária
  - categoria
  - domínio provável da base
- KPIs executivos automáticos
- Gráficos interativos com Plotly
- Insights automáticos sem depender de API externa
- AI BI Assistant opcional com Groq
- Exportação Excel
- Exportação PDF executivo
- Sidebar com navegação real
- Modo debug para inspeção técnica

---

## 🛠 Stack

- Python
- Streamlit
- Pandas
- Plotly
- OpenPyXL
- ReportLab
- python-dotenv
- Groq API opcional

---

## 📂 Estrutura principal

```text
dataflow-bi-automation/
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── .env.example
├── assets/
│   └── styles.py
├── components/
│   ├── ai_assistant.py
│   ├── charts.py
│   ├── chat_message.py
│   ├── insights.py
│   ├── kpis.py
│   ├── sidebar.py
│   └── tables.py
├── services/
│   ├── analytics.py
│   ├── exporter.py
│   ├── formatter.py
│   ├── insight_engine.py
│   ├── llm_router.py
│   ├── loader.py
│   ├── metrics_engine.py
│   ├── schema_analyzer.py
│   └── providers/
│       └── groq_provider.py
└── data/
    └── raw/
        └── vendas.xlsx
```

---

## 🚀 Como rodar

### 1. Instale as dependências

```bash
pip install -r requirements.txt
```

### 2. Rode o app

```bash
streamlit run app.py
```

Ou no Windows:

```bash
run.bat
```

---

## 🤖 Ativar IA opcional

Crie um arquivo `.env` na raiz do projeto com base no `.env.example`:

```env
GROQ_API_KEY=sua_chave_aqui
GROQ_MODEL=llama-3.1-8b-instant
```

Sem a chave, o dashboard continua funcionando normalmente com os insights automáticos locais.

---

## 📌 Observação técnica

A versão atual usa um núcleo mais universal: o carregador preserva as colunas originais da planilha e o `schema_analyzer.py` decide a semântica dos dados. Isso evita forçar toda base para o modelo fixo de vendas.

---

## 👨‍💻 Autor

Júlio Silva  
GitHub: https://github.com/juliosilva244

---

## 📄 Licença

Projeto disponível para fins educacionais, demonstração profissional e portfólio.
