# DataFlow Fusion Ultimate 2.0

Aplicação local de Business Intelligence em Python e Streamlit para ingestão segura,
normalização, análise e exportação de dados comerciais. O projeto reúne oito áreas:
Visão Geral, Análise de Vendas, Produtos, Lojas, Inteligência Artificial, Qualidade dos
Dados, Relatórios e Configurações.

> Versão estável: **IA-geracao-20261023.6**, auditoria **IA-auditoria-20261023.3**.
> Esta distribuição pública contém código, testes com dados controlados e uma base
> sintética; não contém a base operacional nem relatórios internos. A publicação depende
> de confirmação do proprietário. Homologação real da Groq nesta revisão e deploy em
> produção continuam pendentes. Veja [notas da versão](docs/RELEASE_IA6_AUDIT3.md).

## Problema e objetivo

O DataFlow transforma arquivos CSV/XLSX heterogêneos em uma visão analítica consistente,
sem esconder perdas de qualidade ou anomalias monetárias. O fluxo local cobre carga,
validação, filtros, comparação temporal, indicadores e relatórios.

## Funcionalidades confirmadas

- schema canônico, aliases e normalização centralizados;
- tratamento de datas, nulos e valores monetários brasileiros;
- soma monetária exata com `Decimal` nos indicadores e relatórios;
- períodos comparativos equivalentes e filtros compartilhados;
- KPIs, rankings, gráficos Plotly e tabelas paginadas;
- auditoria de registros válidos, descartados, duplicados e motivos de rejeição;
- exportações CSV (ZIP), Excel e PDF com neutralização de fórmulas;
- validação estrutural e limites configuráveis para uploads CSV/XLSX;
- caches isolados por sessão, telemetria local e exportação sob demanda;
- assistente Groq opcional com consentimento, anonimização, timeout, tentativas e limites;
- interface dark responsiva com oito destinos de navegação.

## Tecnologias e arquitetura

Python 3.11, Streamlit, Pandas, Plotly, OpenPyXL e ReportLab.

```text
app.py / main.py       composição e ponto de entrada
components/            páginas e componentes Streamlit
domain/                schema, normalização, modelos e períodos
services/              carga, métricas, segurança, IA e relatórios
services/providers/    adaptadores de provedores externos
data/demo/             dados públicos, sintéticos e determinísticos
scripts/               ferramentas reproduzíveis
tests/                 testes unitários e de integração local
docs/                  arquitetura, segurança e publicação
```

Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Instalação

Requisitos: Python 3.11 (ambiente validado: 3.11.9). No PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para desenvolvimento: `python -m pip install -r requirements-dev.txt`.
Para reproduzir o ambiente validado Windows/Python 3.11, em vez das instalações acima:
`python -m pip install -r requirements-lock-py311-windows.txt` (inclui ferramentas de teste).

As dependências diretas estão fixadas nas versões validadas. O arquivo
`requirements-lock-py311-windows.txt` reproduz o candidato aprovado em Windows/Python
3.11. Snapshots locais de rollback não fazem parte da distribuição pública. O lock ainda
não possui hashes de distribuição; isso permanece uma limitação para produção.

## Configuração e execução

O ponto oficial é `main.py`:

```powershell
Copy-Item .env.example .env
python -m streamlit run main.py --server.port 8510
```

Abra `http://localhost:8510`. O `.env` é opcional e nunca deve ser versionado. Sem chave
de IA, todo o dashboard funciona; somente o assistente externo fica indisponível.
Cada usuário informa sua própria chave Groq no campo mascarado da página **Inteligência
Artificial**. A chave permanece apenas na memória da sessão, pode ser substituída/removida
e não deve ser colocada no `.env`.
`DATAFLOW_DISPLAY_NAME` personaliza a saudação sem embutir identidade no código.

## Dados e demonstração segura

Campos obrigatórios: `Data`, `Loja`, `Produto`, `Quantidade` e `Faturamento`. `Pedido`,
`Categoria`, `Lucro` e `Preço Unitário` são opcionais. Valores podem usar `R$ 1.234,56`.

Para demonstrar, faça upload de [`data/demo/vendas_demo.csv`](data/demo/vendas_demo.csv).
São 720 registros 100% fictícios, com seed fixa, separados da base operacional. Regenere
com `python -m scripts.generate_demo_data`.

Sem upload, a aplicação tenta `data/raw/vendas.xlsx`. A distribuição pública não inclui
essa base: a mensagem de arquivo padrão ausente é esperada no primeiro acesso. Abra
**Dados** na barra superior e envie o CSV demo para carregar o dashboard. Não copie uma
base real para o repositório. O comportamento local com base própria foi preservado.

## Testes e qualidade

```powershell
python -m pytest
python -m ruff check .
python -m compileall -q app.py main.py assets components domain services scripts tests
python -m pip check
```

O benchmark local é `python -m benchmarks.benchmark_pipeline`. Esses comandos não enviam
dados a serviços externos.

A suíte pública usa fixtures controladas e a demonstração sintética. Regressões locais
que dependem da base operacional, dos seus totais ou do seu estado visual não são
distribuídas; permanecem preservadas localmente. Os 357 testes históricos aprovados não
devem ser confundidos com a contagem desta seleção pública. Os testes AppTest não
substituem inspeção visual real em navegador.

## Segurança, privacidade e IA

Uploads são validados por conteúdo e estrutura, incluindo limites e proteções XLSX/ZIP.
Mensagens públicas não expõem detalhes técnicos; logs locais são sanitizados. HTML
dinâmico é escapado e células exportadas são protegidas contra fórmulas.

A IA requer configuração, ativação e consentimento explícito. A anonimização é padrão, e
o provedor recebe pergunta, histórico curto e agregados — nunca o DataFrame completo.
Consulte [docs/SECURITY.md](docs/SECURITY.md).

## Capturas

Capturas existentes exigem revisão de conteúdo/autorização. O roteiro está em
[`docs/screenshots/README.md`](docs/screenshots/README.md); mockups não devem ser
apresentados como telas reais.

## Limitações conhecidas

- nenhuma implantação em nuvem foi homologada nesta preparação; o README remoto
  anterior anuncia um app no Streamlit Cloud, cuja situação e autoatualização não
  foram verificadas — conferir antes do push;
- a integração externa disponível é Groq e exige credencial própria;
- a base operacional não é candidata automática à publicação;
- a auditoria não substitui monitoramento contínuo de novos avisos;
- o lock não contém hashes de distribuição;
- a aprovação visual foi declarada pelo proprietário; não há novas capturas públicas
  nem uma nova inspeção independente nesta preparação;
- a geração real Groq da revisão `.6` ainda requer teste autorizado;
- dados e imagens em commits antigos precisam de revisão de privacidade: removê-los da
  versão atual não os apaga do histórico Git.

## Autoria e licença

Projeto **DataFlow Fusion Ultimate 2.0**. A [licença MIT](LICENSE) já existente no
repositório remoto foi preservada, incluindo seu aviso de copyright. Dados pessoais de
contato e bases operacionais não integram esta distribuição.

English documentation: [README_EN.md](README_EN.md).
