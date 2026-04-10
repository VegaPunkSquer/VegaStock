import sqlite3

# Conecta no seu banco atual
conexao = sqlite3.connect("estoque.db")
cursor = conexao.cursor()

try:
    # O comando mágico que injeta a coluna sem apagar nada
    cursor.execute("ALTER TABLE movimentacoes_estoque ADD COLUMN custo_unitario FLOAT;")
    conexao.commit()
    print("Sucesso! Coluna 'custo_unitario' adicionada. Pode deletar este arquivo.")
except Exception as e:
    print(f"Erro (ou a coluna já existe): {e}")

conexao.close()