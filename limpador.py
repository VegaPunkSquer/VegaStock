import os
from dotenv import load_dotenv

# Força o caminho absoluto para achar o cofre, independente de onde o terminal estiver
caminho_atual = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(caminho_atual, ".env"))

from database import SessionLocal
from models import MovimentacaoEstoque

db = SessionLocal()
# Deleta TODAS as movimentações de estoque para zerar a tabela
db.query(MovimentacaoEstoque).delete()
db.commit()
print("Banco de dados limpo! As movimentações fantasmas sumiram.")