from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import SessionLocal
import models
import schemas
import hashlib

app = FastAPI(title="SaaS Restaurante - Estoque API")

# Dependência para abrir e fechar a conexão com o banco a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. Endpoint: White-Label (Cor e Logo)
@app.get("/config/{cliente_id}", response_model=schemas.ClienteConfig)
def get_config(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

# 2. Endpoint: Listar Estoque do Cliente
@app.get("/produtos", response_model=List[schemas.ProdutoResponse])
def listar_produtos(cliente_id: int, db: Session = Depends(get_db)):
    # A cláusula multitenant em ação: só traz os produtos daquele restaurante
    produtos = db.query(models.Produto).filter(models.Produto.cliente_id == cliente_id).all()
    return produtos

# 3. Endpoint Crítico: Dar Baixa / Movimentação
@app.post("/movimentacao")
def registrar_movimentacao(mov: schemas.MovimentacaoCreate, db: Session = Depends(get_db)):
    # Localizar o produto e confirmar que pertence ao cliente
    produto = db.query(models.Produto).filter(
        models.Produto.id == mov.produto_id,
        models.Produto.cliente_id == mov.cliente_id
    ).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado no estoque deste cliente")

    # Localizar o motivo
    motivo = db.query(models.MotivoBaixa).filter(
        models.MotivoBaixa.id == mov.motivo_baixa_id,
        models.MotivoBaixa.cliente_id == mov.cliente_id
    ).first()

    if not motivo:
        raise HTTPException(status_code=404, detail="Motivo de baixa inválido")

    # Deduzir ou somar do saldo baseado no tipo de motivo (NEGATIVO/POSITIVO)
    tipo_movimento = "SAIDA" if motivo.tipo == "NEGATIVO" or "Venda" in motivo.descricao else "ENTRADA"
    
    if tipo_movimento == "SAIDA":
        produto.quantidade_atual -= mov.quantidade
    else:
        produto.quantidade_atual += mov.quantidade

    # Gravar o registro no histórico
    nova_movimentacao = models.MovimentacaoEstoque(
        cliente_id=mov.cliente_id,
        produto_id=mov.produto_id,
        motivo_baixa_id=mov.motivo_baixa_id,
        tipo_movimento=tipo_movimento,
        quantidade=mov.quantidade
    )

    db.add(nova_movimentacao)
    db.commit()
    
    return {"status": "sucesso", "novo_saldo": produto.quantidade_atual}

# 4. Endpoint: Relatório de Desperdício (A isca de vendas)
@app.get("/relatorios/desperdicio")
def relatorio_desperdicio(cliente_id: int, db: Session = Depends(get_db)):
    # Busca todas as movimentações onde o motivo é de perda (NEGATIVO)
    movimentacoes = db.query(models.MovimentacaoEstoque).join(
        models.MotivoBaixa, models.MovimentacaoEstoque.motivo_baixa_id == models.MotivoBaixa.id
    ).filter(
        models.MovimentacaoEstoque.cliente_id == cliente_id,
        models.MotivoBaixa.tipo == "NEGATIVO"
    ).all()

    resultados = []
    for mov in movimentacoes:
        produto = db.query(models.Produto).filter(models.Produto.id == mov.produto_id).first()
        motivo = db.query(models.MotivoBaixa).filter(models.MotivoBaixa.id == mov.motivo_baixa_id).first()
        
        # Calcula a grana perdida: Quantidade desperdiçada * Custo daquele produto
        custo_perdido = mov.quantidade * produto.custo_medio

        resultados.append({
            "produto": produto.nome,
            "quantidade_perdida": mov.quantidade,
            "unidade": produto.unidade_medida,
            "motivo": motivo.descricao,
            "custo_total_perdido_rs": round(custo_perdido, 2)
        })

    return resultados

# Função interna para gerar a criptografia (Hash)
def gerar_hash(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()

@app.post("/cadastrar")
def cadastrar_restaurante(dados: schemas.CadastroRequest, db: Session = Depends(get_db)):
    # 1. Validar a Licença (Compara o Hash)
    hash_token = gerar_hash(dados.token_licenca)
    licenca = db.query(models.Licenca).filter(models.Licenca.token == hash_token, models.Licenca.usada == False).first()
    
    if not licenca:
        raise HTTPException(status_code=400, detail="Licença inválida ou já utilizada.")
    
    # NOVAS TRAVAS DE SEGURANÇA
    if licenca.cnpj_esperado != dados.cnpj:
        raise HTTPException(status_code=400, detail="Esta licença não foi emitida para este CNPJ.")
        
    if licenca.data_expiracao < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Licença expirada (prazo de 48h esgotado).")
    
    # 2. Verificar se CNPJ ou Login já existem para evitar duplicidade
    if db.query(models.Cliente).filter(models.Cliente.cnpj == dados.cnpj).first():
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")
    if db.query(models.Usuario).filter(models.Usuario.login == dados.login).first():
        raise HTTPException(status_code=400, detail="Nome de usuário já em uso.")

    # 3. Criar o "Bloco" do Cliente
    novo_cliente = models.Cliente(
        nome_fantasia=dados.nome_fantasia, 
        cnpj=dados.cnpj,
        logo_url=dados.logo_url  # NOVA LINHA: Gravando no banco
    )

    # 4. Criar o Usuário Admin trancado dentro do bloco
    novo_usuario = models.Usuario(
        cliente_id=novo_cliente.id,
        login=dados.login,
        senha=gerar_hash(dados.senha),
        nivel_acesso="Admin"
    )
    db.add(novo_usuario)

    # 5. Queimar a Licença (Marca como usada e atrela ao cliente)
    licenca.usada = True
    licenca.cliente_id = novo_cliente.id

    db.commit()
    return {"status": "sucesso", "mensagem": "Restaurante cadastrado com sucesso!"}

@app.post("/login")
def fazer_login(dados: schemas.LoginRequest, db: Session = Depends(get_db)):
    # Criptografa a senha digitada e compara com a que está no banco
    senha_hash = gerar_hash(dados.senha)
    usuario = db.query(models.Usuario).filter(
        models.Usuario.login == dados.login,
        models.Usuario.senha == senha_hash
    ).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")

    # Puxa os dados do restaurante (bloco) atrelado a este usuário
    cliente = db.query(models.Cliente).filter(models.Cliente.id == usuario.cliente_id).first()

    # Devolve a chave do cofre para o PySide
    return {
        "status": "sucesso",
        "cliente_id": cliente.id,
        "nome_fantasia": cliente.nome_fantasia,
        "nivel_acesso": usuario.nivel_acesso
    }