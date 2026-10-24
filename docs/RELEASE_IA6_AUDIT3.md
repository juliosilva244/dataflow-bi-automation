# Versão estável DataFlow Fusion Ultimate 2.0

- Geração: `IA-geracao-20261023.6`.
- Auditoria: `IA-auditoria-20261023.3`.
- Estado da IA: `IA-estado-20261023.2` (marcador independente, não uma revisão antiga de geração).
- Entrada oficial: `python -m streamlit run main.py --server.port 8510`.
- Ambiente anteriormente validado: Windows, Python 3.11.9, Streamlit 1.66.1 e Pillow 13.0.0.

## Funcionalidades desta distribuição

Oito áreas funcionais, schema e normalização centralizados, cálculos monetários Decimal,
comparações temporais explícitas, anomalias preservadas, qualidade de dados verificável,
gráficos Plotly, paginação, caches por sessão e exportações CSV/Excel/PDF. O assistente
Groq é opcional, com BYOK temporário por sessão, consentimento, anonimização, limites e
tratamento seguro de falhas. Nenhuma funcionalidade da aplicação foi alterada para preparar
esta distribuição.

Única adequação de apresentação por privacidade: a prévia de formatação em Configurações
passou a usar um exemplo explicitamente fictício. Nenhum KPI, valor de dataset, cálculo,
regra de segurança, integração ou comportamento de preferências foi alterado.

## Evidências e limites

A auditoria local anterior registrou **357 testes aprovados em 36,70 s**, Ruff,
compilação e pip check aprovados. A auditoria dedicada de dependências de 23/10/2026
não encontrou vulnerabilidades conhecidas na fonte consultada, sem forçar dependências.
São evidências históricas; a suíte completa e as consultas de CVEs não foram refeitas
somente para preparar esta publicação. Não se presume que essa contagem corresponda à
seleção pública de testes.

A aprovação visual é uma declaração do proprietário. Nenhuma nova inspeção gráfica,
captura final ou chamada real à Groq foi feita nesta preparação. A homologação externa
específica da revisão `.6` permanece pendente; respostas históricas de outras revisões
não a substituem. AppTest verifica execução e navegação, não aparência no Chrome.

## Conteúdo público e preservação local

Incluídos: código atual, configuração sem segredos, dependências correntes, documentação
pública, testes controlados e `data/demo/vendas_demo.csv` sintético. A licença MIT do
repositório existente é mantida sem alteração dos termos.

Excluídos: ambientes virtuais, arquivos de segredo, bases operacionais, uploads, logs,
temporários, backups, checkpoints, relatórios internos, imagens não revisadas, locks
antigos/candidatos redundantes e testes ligados à base operacional ou a seus totais.
Nenhum desses arquivos locais é apagado. Os testes públicos adicionais usam a demo,
isolam a carga no AppTest e bloqueiam clientes externos durante os testes.

No primeiro acesso de uma instalação pública, abra **Dados** e envie o CSV demo.
É esperada a mensagem de base padrão ausente até o upload, sem alterar o comportamento
local existente. Não há deploy em nuvem homologado nesta preparação nem autenticação
multiusuário de produção; o lock ainda não contém hashes de distribuição. O README remoto
anterior anuncia um app Streamlit Cloud. Seu estado e possível atualização automática
por push precisam ser confirmados pelo proprietário; o serviço não foi acessado aqui.

## Git e privacidade histórica

A preparação parte da `main` remota existente, não cria história independente nem
substitui arquivos locais por uma cópia antiga. A branch
`improvements/security-quality-2026` permanece intacta; não há merge automático dela.

A `main` anterior já contém uma base operacional e imagens. A próxima árvore remove
esses itens da distribuição atual, mas **o histórico continua acessível**. Esta operação
não altera commits antigos, não revoga arquivos previamente públicos e não usa force push.
O proprietário deve revisar essa exposição histórica separadamente antes de autorizar
a publicação. Não foi feita avaliação visual do conteúdo das imagens históricas.

Publicação do código não equivale a aprovação de deploy em produção. O commit e o push
só podem ocorrer após confirmação do proprietário e nova conferência da ponta remota.

## Verificações de preparação em 24/10/2026

- 82 testes da seleção pública aprovados em 62,56 s.
- 23 testes aprovados em 7,95 s numa exportação limpa do índice, sem base operacional;
  incluem os oito destinos AppTest, CSV/Excel/PDF, demo e proteções. Há sobreposição
  com os 82 testes; não são 105 casos independentes.
- Ruff dos módulos da aplicação e arquivos públicos de teste aprovado; pip check aprovado.
- Todos os arquivos Python preparados compilados em memória, sem executar os seus corpos.
- Revisão de todos os blobs do índice e dos arquivos rastreados ignorados, sem alertas
  nos padrões de credenciais verificados. A revisão adicional retirou o exemplo operacional
  fixado na prévia; não há literals monetários operacionais conhecidos na árvore preparada.
- Leitura dos 65 blobs do histórico remoto disponível sem alerta nos mesmos padrões de
  credenciais. A presença histórica da base e das imagens, porém, continua comprovada.

A checagem padrão de whitespace sinalizou CRLF e linhas finais vazias já existentes.
A checagem compatível com CRLF, aceitando essas linhas finais, passou; o código estável
não foi reformatado apenas para eliminar avisos de estilo. Nenhum destes resultados é
uma nova auditoria de CVEs, uma chamada real Groq ou uma homologação visual no navegador.
