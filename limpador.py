import os
from dotenv import load_dotenv

# Força o caminho absoluto para achar o cofre, não importa de onde o terminal rode
caminho_atual = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(caminho_atual, ".env"))

from database import SessionLocal
from models import MovimentacaoEstoque, Produto

db = SessionLocal()

# Deleta TODAS as movimentações de estoque E zera as quantidades
try:
    linhas_apagadas = db.query(MovimentacaoEstoque).delete()
    
    # O Pulo do Gato: Zera o estoque e o preço de todos os produtos do catálogo
    produtos_zerados = db.query(Produto).update({
        Produto.quantidade_atual: 0.0,
        Produto.custo_medio: 0.0
    })
    
    db.commit()
    print(f"Sucesso! {linhas_apagadas} movimentações vaporizadas e {produtos_zerados} produtos zerados.")
except Exception as e:
    db.rollback()
    print(f"Erro ao limpar: {e}")