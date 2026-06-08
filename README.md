# 🚀 DataFlow BI Automation

**Plataforma de Business Intelligence em Python para transformar planilhas Excel/CSV em dashboards executivos, KPIs automáticos, análise de schema, insights e relatórios exportáveis.**

O **DataFlow BI Automation** foi desenvolvido como um projeto profissional de portfólio em Dados/BI, com foco em automação analítica, dashboards executivos, análise automática de bases tabulares e geração de relatórios em Excel/PDF.

---

## 📌 Visão geral

Empresas pequenas, áreas administrativas e equipes operacionais ainda dependem muito de planilhas manuais para monitorar vendas, desempenho, produtos, lojas, volume, receita e indicadores.

O **DataFlow BI Automation** resolve esse problema automatizando o processo de análise:

1. o usuário envia uma planilha `.xlsx`, `.xls` ou `.csv`;
2. o sistema identifica automaticamente colunas relevantes;
3. a aplicação detecta métrica principal, coluna de data, dimensões e domínio provável da base;
4. KPIs e gráficos são gerados automaticamente;
5. insights locais são exibidos sem depender obrigatoriamente de IA externa;
6. relatórios podem ser exportados em Excel e PDF executivo.

---

## 🎯 Objetivo do projeto

O objetivo do projeto é demonstrar uma solução prática de BI com Python, capaz de transformar dados tabulares em uma experiência visual, analítica e exportável.

O projeto foi pensado para:

* portfólio profissional em Dados/BI;
* demonstração de automação analítica;
* análise rápida de planilhas empresariais;
* geração automática de dashboards;
* criação de relatórios executivos;
* estudo de arquitetura modular com Streamlit, Pandas e Plotly.

---

## ✨ Principais recursos

* Upload de arquivos `.xlsx`, `.xls` e `.csv`
* Base padrão de demonstração
* Detecção automática de schema
* Identificação automática de:

  * métrica principal
  * coluna de data
  * dimensão principal
  * dimensão secundária
  * categoria
  * coluna temporal
  * domínio provável da base
* KPIs executivos automáticos
* Gráficos interativos com Plotly
* Insights automáticos locais
* AI BI Assistant opcional com Groq
* Exportação para Excel
* Exportação para PDF executivo
* Barra lateral com navegação real
* Modo debug para inspeção técnica
* Layout escuro com aparência de painel SaaS

---

## 🧠 Detecção automática de schema

Um dos diferenciais do DataFlow é o uso de um núcleo mais universal para interpretação de planilhas.

Em vez de obrigar toda base a seguir um modelo fixo, o sistema preserva as colunas originais e usa o `schema_analyzer.py` para inferir a função de cada coluna.

O sistema tenta identificar automaticamente:

| Tipo detectado      | Exemplo                      |
| ------------------- | ---------------------------- |
| Coluna temporal     | Data, Período, Mês           |
| Métrica principal   | Faturamento, Receita, Valor  |
| Dimensão principal  | Loja, Cliente, Região        |
| Dimensão secundária | Produto, Categoria, Serviço  |
| Quantidade          | Quantidade, Volume, Unidades |
| Domínio provável    | Vendas, Operações, Genérico  |

Isso permite que o projeto seja mais flexível do que um painel fixo feito apenas para uma planilha específica.

---

## 📊 KPIs gerados automaticamente

A aplicação gera indicadores executivos com base no schema detectado, incluindo:

* faturamento total;
* ticket médio;
* total de registros analisados;
* quantidade total;
* dimensão principal mais relevante;
* dimensão secundária mais relevante;
* pontuação de confiança do schema.

---

## 📈 Visualização

O dashboard gera gráficos interativos com Plotly, como:

* evolução da métrica ao longo do tempo;
* classificação por dimensão principal;
* classificação por dimensão secundária;
* análise por loja;
* análise por produto;
* tabelas resumidas para exploração dos dados.

---

## 📤 Exportações

O DataFlow permite exportar os resultados da análise em dois formatos:

### Excel

O relatório Excel é voltado para auditorias e análises detalhadas. Ele pode conter várias abas, como:

* base preparada;
* KPIs;
* qualidade do schema;
* schema detectado;
* faturamento por mês;
* faturamento por loja;
* melhores produtos;
* faturamento por dia;
* resumo por dimensão principal;
* resumo por dimensão secundária.

### PDF

O relatório PDF é voltado para leitura executiva. Ele apresenta:

* visão geral da análise;
* domínio detectado;
* métrica principal;
* dimensões principais;
* KPIs executivos;
* pontuação do schema;
* rankings e resumos financeiros;
* tabelas com valores formatados em reais.

---

## 🤖 Assistente de IA BI opcional

O projeto possui integração opcional com a API da Groq.

Quando configurado, o assistente pode apoiar análises e perguntas sobre os dados. Sem chave de API, o dashboard continua funcionando normalmente com os insights locais.

Exemplo de `.env`:

```env
GROQ_API_KEY=sua_chave_aqui
GROQ_MODEL=llama-3.1-8b-instant
```

---

## 🛠️ Pilha utilizada

* Python
* Streamlit
* Pandas
* Plotly
* OpenPyXL
* ReportLab
* python-dotenv
* API Groq opcional

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

## 🚀 Como rodar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/juliosilva244/dataflow-bi-automation.git
```

### 2. Acessar a pasta

```bash
cd dataflow-bi-automation
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Rodar o aplicativo

```bash
streamlit run app.py
```

Ou, no Windows:

```bash
run.bat
```

Depois acesse no navegador:

```text
http://localhost:8501
```

---

## 🧪 Validação local

Comandos usados para validar o projeto:

```bash
python -m compileall assets components services src app.py main.py
pip install -r requirements.txt
python -m streamlit run app.py
```

Status validado:

* aplicação sobe localmente;
* dependências instaladas corretamente;
* arquivos Python compilam sem erro;
* exportação Excel funcional;
* exportação PDF funcional;
* avisos antigos do Streamlit corrigidos.

---

## 📌 Diferenciais técnicos

* Arquitetura modular separada por componentes e serviços.
* Analisador de schema para interpretar colunas automaticamente.
* Métricas calculadas dinamicamente.
* Exportador Excel/PDF desacoplado.
* Layout visual customizado para aparência de dashboard executivo.
* IA opcional sem tornar o projeto dependente de API externa.
* Base padrão para demonstração imediata.
* Estrutura preparada para evolução futura com filtros avançados, deploy e BI Assistant mais robusto.

---

## 🧭 Possíveis evoluções

* Deploy online com Streamlit Community Cloud.
* Inclusão de screenshots e GIF demonstrativo.
* Filtros avançados por período, loja, produto e categoria.
* Gráficos adicionais, como donut chart e análise comparativa.
* Relatório PDF com gráficos incorporados.
* Camada de perguntas em linguagem natural sobre os dados.
* Suporte a múltiplos arquivos e comparação entre períodos.
* Sistema de templates por domínio de negócio.

---

## 👨‍💻 Autor

**Júlio Silva**
GitHub: https://github.com/juliosilva244

---

## 📄 Licença

Projeto desenvolvido para fins educacionais, demonstração profissional, portfólio em Dados/BI e validação de conceitos de automação analítica com Python.
