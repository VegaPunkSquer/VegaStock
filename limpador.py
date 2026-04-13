from database import SessionLocal
from models import MovimentacaoEstoque

db = SessionLocal()
# Deleta TODAS as movimentações de estoque para zerar a tabela
db.query(MovimentacaoEstoque).delete()
db.commit()
print("Banco de dados limpo! As movimentações fantasmas sumiram.")