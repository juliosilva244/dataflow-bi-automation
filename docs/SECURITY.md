# Segurança e publicação responsável

## Modelo operacional

O DataFlow é uma aplicação local. Não publique bases, logs, relatórios ou credenciais. A
IA externa é opcional e deve permanecer desativada quando dados não puderem sair do
ambiente controlado.

## Controles existentes

- limites de bytes, linhas, colunas e estrutura para CSV/XLSX;
- mitigação de ZIP bombs em XLSX;
- schema canônico e rejeição de colunas ambíguas;
- mensagens públicas sem stack trace e logs sanitizados;
- escape de conteúdo dinâmico e neutralização de fórmulas em exportações;
- consentimento, ativação, anonimização, timeout, tentativas, rate limit e tokens para IA;
- caches de dados isolados por sessão.

## Segredos

Cada usuário informa a chave Groq em campo mascarado; ela fica apenas no
`st.session_state`, não em arquivo, banco, URL, log ou cache compartilhado. Trocar/remover
a chave revoga o consentimento e invalida o status anterior. Nunca preencha `.env.example`
com valores reais. `.env`, `.streamlit/secrets.toml`, certificados e chaves privadas são
ignorados. Revise o índice do Git, pois `.gitignore` não remove arquivos já rastreados.

## Dados

`data/raw/`, uploads, logs, temporários, relatórios e artefatos não são publicáveis por
padrão. `data/demo/vendas_demo.csv` é a única base preparada para publicação: é sintética,
determinística e identificada por pedidos `DEMO-*`.

## Auditoria de dependências

Em 23/10/2026, `pip-audit 2.10.1` foi executado somente pelo ambiente temporário isolado.
Streamlit 1.66.1 passou a declarar `Pillow>=9.2.0,<14`, permitindo Pillow 13.0.0 sem
forçar metadados ou usar `--no-deps`. A auditoria direta dos 59 pacotes instalados e as
auditorias de `requirements.txt`, `requirements-dev.txt` e do lock completo não
encontraram vulnerabilidades conhecidas na base consultada. O candidato também passou em
169 testes, Ruff, compilação e `pip check`. Evidências JSON ficam em
`outputs/security/`, pasta não publicável. Isso é um retrato datado, não garantia contra
avisos futuros.

## Checklist de divulgação

1. Revisar todo o conjunto candidato e o histórico Git por segredos.
2. Confirmar que a base operacional e artefatos nunca foram adicionados ao índice.
3. Executar scanner de CVEs e resolver ou aceitar riscos formalmente.
4. Revisar screenshots quanto a nomes, caminhos, dados e notificações.
5. Preservar a licença MIT e o copyright já existentes no remoto; não incluir novos
   dados pessoais ou capturas sem autorização.
6. Executar testes e uma instalação limpa antes do primeiro push.

Relate vulnerabilidades diretamente ao proprietário; não abra uma issue pública contendo
segredos ou dados operacionais.

## Limites da preparação pública

Documentos internos e testes vinculados a valores operacionais permanecem locais.
Somente a demonstração sintética e testes controlados devem ser distribuídos. Revise o
índice e os blobs do commit, além do `.gitignore`: a base operacional já estava rastreada
na `main` remota antes desta preparação. Sua remoção da próxima árvore não apaga commits
antigos; não foi feita reescrita de histórico nem push forçado. É necessária revisão do
proprietário sobre o conteúdo histórico. A branch remota de melhorias é preservada.

A ausência de alertas em uma varredura local por padrões não prova ausência universal
de segredos. A homologação real da Groq da revisão `.6` e qualquer implantação em
produção continuam separadas da publicação do código e dependem de aprovação apropriada.
