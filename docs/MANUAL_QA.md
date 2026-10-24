# Homologação manual da distribuição pública

Execute `python -m streamlit run main.py --server.port 8510` e abra
`http://localhost:8510`. Use outra porta se ela já estiver ocupada; não encerre processos
sem identificá-los e obter autorização. Em **Dados**, envie `data/demo/vendas_demo.csv`.
Não use a base operacional nem credenciais reais para capturas públicas.

No Chrome, use zoom de 100%. Abra F12, pressione Ctrl+Shift+M, escolha modo responsivo e
informe, uma de cada vez: 1536×1024, 1366×768, 768×1024 e 390×844. A navegação é por
estado de sessão, na mesma URL; não há URLs independentes inventadas para cada página.

| Página | Ações e critérios |
| --- | --- |
| Visão Geral | Conferir KPIs, períodos, tooltips, visão completa/típica e busca por produto/loja; filtros devem manter coerência dos valores. |
| Análise de Vendas | Alternar gráficos e períodos; conferir tabelas e valores integrais. |
| Produtos | Conferir ranking, participação, seleção individual e paginação. |
| Lojas | Conferir ranking, perfil, períodos e paginação; não misturar receita global e individual. |
| Inteligência Artificial | Sem chave, deve ficar desativada; navegar não deve perder o estado da sessão. Não clicar em testar/gerar com chave real sem autorização. |
| Qualidade dos Dados | Conferir recebidos, válidos, descartados, duplicados e motivos; nenhum descarte pode ficar oculto. |
| Relatórios | Gerar CSV/Excel/PDF; abrir arquivos e comparar escopo e totais da demo; conferir fórmulas neutralizadas. |
| Configurações | Alterar preferências, ativação/anonimização e retornar; nova sessão deve começar sem chave e com IA desativada. |

Em todas as páginas: abrir/fechar a sidebar pelo controle nativo, navegar por teclado,
testar filtros e botões, conferir legendas/tooltips, ausência de cortes, sobreposição e
rolagem horizontal indevida. Upload inválido deve produzir mensagem segura, sem traceback.

Registrar resultado, versão, resolução e passos. Enviar capturas reais das oito páginas
em desktop e celular, além de qualquer problema em notebook/tablet. Ocultar dados
pessoais, chaves, notificações e caminhos locais. Não apresentar mockups ou AppTest como
homologação visual real. A geração externa da revisão `.6` continua pendente de teste
expressamente autorizado; não simular sua aprovação.
