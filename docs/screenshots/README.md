# Capturas reais para o portfólio

Esta pasta está preparada, mas não contém capturas aprovadas. A automação gráfica não deve
contornar controles de segurança do Windows.

Para a homologação completa das oito páginas e quatro resoluções, siga também o
[checklist manual público](../MANUAL_QA.md).

## Roteiro manual

1. Execute `streamlit run main.py --server.port 8510` e abra `http://localhost:8510`.
2. Faça upload de `data/demo/vendas_demo.csv`; não capture a base operacional.
3. Use zoom de 100%, feche notificações e confira se não há caminhos, chaves ou dados
   pessoais visíveis.
4. Capture desktop em 1536×1024 e celular em 390×844 (DevTools ou aparelho autorizado).
5. Revise cada imagem antes de movê-la para esta pasta.

Nomes sugeridos: `overview-desktop.png`, `sales-desktop.png`, `products-desktop.png`,
`stores-desktop.png`, `quality-desktop.png`, `reports-desktop.png`,
`settings-desktop.png`, `sidebar-desktop.png` e `overview-mobile.png`.

Somente capturas reais e autorizadas devem ser usadas. A página de IA deve mostrar seu
estado verdadeiro; não simule resposta externa. Registre data, resolução, hash da base
demo e versão do aplicativo na revisão da publicação.
