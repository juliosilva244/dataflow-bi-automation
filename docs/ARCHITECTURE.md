# Arquitetura do DataFlow Fusion Ultimate 2.0

## Visão geral

`main.py` é o ponto oficial e chama `app.main`. A aplicação Streamlit mantém estado de
navegação, preferências, filtros, caches e telemetria por sessão. A apresentação em
`components/` consome modelos e serviços; integrações externas ficam atrás de adaptadores.

```text
CSV/XLSX -> validação -> normalização -> DataFrame canônico -> filtros
                                                    |-> métricas/gráficos
                                                    |-> qualidade
                                                    |-> relatórios
                                                    `-> contexto agregado opcional de IA
```

## Ingestão e validação

`services/upload_security.py` lê no máximo o limite configurado e valida a assinatura e a
estrutura de CSV/XLSX. CSV aceita UTF-8/CP1252 e delimitadores reconhecidos; XLSX é
inspecionado como ZIP para limitar entradas, tamanho descompactado e compressão. O número
de linhas e colunas também é limitado. `services/loader.py` orquestra a leitura, calcula
uma assinatura SHA-256 do conteúdo e registra telemetria sem registrar o conteúdo.

## Schema, normalização e qualidade

`domain/schema.py` define campos, tipos, obrigatoriedade, nulabilidade e aliases. São
obrigatórios Data, Loja, Produto, Quantidade e Faturamento. Pedido, Categoria, Lucro e
Preço Unitário são opcionais. `domain/normalization.py` resolve aliases, interpreta datas,
nulos e números brasileiros, rejeita ambiguidades, remove duplicidades e produz um
`DataQualityReport`. `services/data_quality.py` complementa a auditoria e expõe os motivos
de rejeição; perdas não são ocultadas.

## Motor analítico e períodos

`services/metrics_engine.py` calcula KPIs tipados, agregações e crescimentos. Somas
monetárias exatas usam `Decimal`; conversões para float ficam restritas à compatibilidade
de visualização. `domain/periods.py` divide janelas consecutivas de mesma duração e informa
seus rótulos. Os filtros globais são aplicados antes da construção do estado analítico.

## Interface e estado

`app.py` compõe controles de dados/filtros e despacha uma das oito páginas. A sidebar em
`components/sidebar.py` usa o controle nativo do Streamlit para abrir/fechar e preserva a
página ativa em `st.session_state`. Os dashboards usam Plotly e HTML somente onde o
conteúdo é previamente escapado. `services/preferences.py` controla preferências locais
da sessão; nenhuma persistência multiusuário é implementada.

## Cache, telemetria e desempenho

`services/performance.py` oferece cache LRU com TTL isolado no estado da sessão. Chaves de
leitura dependem da assinatura do arquivo; chaves analíticas dependem do fingerprint dos
dados e parâmetros. Paginação afeta apenas a apresentação. Excel é criado sob demanda e
invalidado quando o estado analítico muda. A telemetria local mede carga, normalização,
agregação e exportação sem conteúdo de dados.

## Relatórios

`services/reporting.py` constrói documentos de relatório e exporta CSV compactado, XLSX e
PDF. `services/exporter.py` mantém a exportação executiva legada. Ambos neutralizam textos
que planilhas poderiam interpretar como fórmulas. O XLSX inclui qualidade e preserva
valores monetários exatos como texto quando excedem a precisão segura da planilha.

## Governança de IA

`components/ai_assistant.py` só solicita resposta quando IA está ativada e há consentimento.
`services/llm_router.py` impõe essas condições, anonimiza identificadores, reduz o payload
a agregados/pergunta/histórico curto e aplica limite de requisições. O adaptador
`components/ai_assistant.py` recebe a chave individual em campo mascarado e a mantém
somente no `st.session_state`. Substituição ou remoção invalida consentimento e status de
conexão anteriores. `services/providers/groq_provider.py` recebe a chave explicitamente,
sem fallback para `GROQ_API_KEY` global, e configura timeout, repetição e limite de tokens.
Ausência de configuração não bloqueia a aplicação.

## Segurança e falhas

Exceções esperadas viram mensagens públicas estáveis; detalhes técnicos vão para logs
locais sanitizados e rotativos. `services/security.py` centraliza escape e proteção contra
fórmulas. Não há banco, API pública, autenticação, autorização por usuário ou armazenamento
central de sessões.

## Limitações confirmadas

- execução local Streamlit; nenhuma topologia de nuvem está configurada;
- cache e preferências vivem apenas na sessão/processo;
- Groq é o único provedor externo implementado;
- a origem da base operacional precisa de revisão antes de publicação;
- aprovação visual declarada pelo proprietário, sem novas capturas públicas nesta
  preparação; a homologação real da Groq na revisão `.6` permanece pendente;
- a auditoria de CVEs de 23/10/2026 passou; nenhuma nova consulta foi feita nesta preparação.
