import pandas as pd
import random
from datetime import datetime, timedelta

# =========================================================
# CONFIGURAÇÕES
# =========================================================

lojas = [
    "Loja Centro",
    "Loja Norte",
    "Loja Sul",
    "Loja Oeste",
    "Loja Leste"
]

produtos = [
    "Notebook",
    "Mouse",
    "Teclado",
    "Monitor",
    "Headset",
    "Cadeira Gamer"
]

# =========================================================
# GERAR DADOS
# =========================================================

dados = []

data_inicial = datetime(2024, 1, 1)

for i in range(500):

    loja = random.choice(lojas)
    produto = random.choice(produtos)

    quantidade = random.randint(1, 10)

    preco = random.randint(100, 5000)

    faturamento = quantidade * preco

    data = data_inicial + timedelta(days=random.randint(0, 180))

    dados.append({
        "Data": data,
        "Loja": loja,
        "Produto": produto,
        "Quantidade": quantidade,
        "Preço Unitário": preco,
        "Faturamento": faturamento
    })

# =========================================================
# DATAFRAME
# =========================================================

df = pd.DataFrame(dados)

# =========================================================
# EXPORTAR EXCEL
# =========================================================

df.to_excel(
    "data/raw/vendas.xlsx",
    index=False
)

print("Arquivo vendas.xlsx gerado com sucesso.")