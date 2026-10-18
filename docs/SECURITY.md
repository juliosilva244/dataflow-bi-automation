# Segurança e confiabilidade

## Alterações iniciais
- Neutralização de texto com aparência de fórmula em exportações Excel.
- Escape de texto inserido nos parágrafos de tabelas PDF.
- Limite configurável de tamanho do upload (DATAFLOW_MAX_UPLOAD_MB, padrão 25).
- Mensagens genéricas ao usuário e logs internos para falhas inesperadas.
- Papéis permitidos no histórico da IA e limite de caracteres.
- Testes básicos de regressão e workflow de CI.

## Pendências
- Limites de linhas, colunas, descompressão de XLSX e memória.
- Revisão de isolamento dos dados entre sessões e cache.
- Auditoria de dependências e lockfile reproduzível.
- Testes de integração e execução manual do aplicativo.

Não utilizar esta revisão como certificação de segurança. Faça validação antes de publicar.
