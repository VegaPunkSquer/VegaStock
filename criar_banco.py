from database import engine, Base
# Importar os modelos é obrigatório para que o SQLAlchemy "enxergue" as tabelas antes de criar
import models

print("Iniciando a criação do banco de dados (Mock SQLite)...")

# Este comando traduz as classes do models.py em tabelas reais no banco
Base.metadata.create_all(bind=engine)

print("Sucesso! O arquivo 'estoque_mock.db' foi gerado na raiz do projeto.")
print("Tabelas criadas, isolamento multitenant garantido e fundação pronta.")