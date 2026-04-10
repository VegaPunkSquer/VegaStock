import sqlite3

# Conecta no seu banco de dados oficial de testes
conexao = sqlite3.connect("estoque_mock.db")
cursor = conexao.cursor()

print("Iniciando atualização do banco de dados...")

try:
    # Injeta a coluna de cargo
    cursor.execute("ALTER TABLE usuarios ADD COLUMN cargo VARCHAR;")
    print("✅ Coluna 'cargo' adicionada com sucesso.")
except Exception as e:
    print(f"⚠️ Aviso (cargo): {e}")

try:
    # Injeta a coluna de permissões com um valor padrão para não quebrar usuários antigos
    cursor.execute("ALTER TABLE usuarios ADD COLUMN permissoes VARCHAR DEFAULT 'dashboard';")
    print("✅ Coluna 'permissoes' adicionada com sucesso.")
except Exception as e:
    print(f"⚠️ Aviso (permissoes): {e}")

conexao.commit()
conexao.close()
print("Processo finalizado! Banco atualizado sem perder dados.")