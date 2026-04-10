from fastapi import FastAPI, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import SessionLocal
import models
import schemas
import hashlib
import requests

app = FastAPI(title="SaaS Restaurante - Estoque API")

# Chave do Sandbox do Asaas (Cole a sua aqui)
ASAAS_API_KEY = "$aact_hmlg_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OmY5NzA0MzRjLTY4NjUtNDNmOS1iN2U1LTk1MmMyYmRlYjVkYTo6JGFhY2hfZDgzODYwMzEtMjIyNy00NDg2LTkzZGMtMzQ3OWM5OTM1Njk3"
ASAAS_URL = "https://sandbox.asaas.com/api/v3"
HEADERS = {
    "access_token": ASAAS_API_KEY,
    "Content-Type": "application/json"
}

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
        logo_url=dados.logo_url
    )
    db.add(novo_cliente)
    db.commit() # Força o banco a gravar fisicamente e gerar o ID real agora
    db.refresh(novo_cliente) # Puxa o ID gerado de volta pro Python

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
        "nivel_acesso": usuario.nivel_acesso,
        "logo_url": cliente.logo_url,  # <-- ESSA É A LINHA QUE FALTAVA
        "status_assinatura": cliente.status_assinatura, # Para saber se é PRO
        "limite_global": cliente.limite_global_notificacao
    }
    
@app.post("/verificar_licenca")
def verificar_licenca(dados: schemas.VerificarLicencaRequest, db: Session = Depends(get_db)):
    token_criptografado = hashlib.sha256(dados.token_licenca.encode()).hexdigest()
    
    licenca = db.query(models.Licenca).filter(
        models.Licenca.token == token_criptografado,
        models.Licenca.cnpj_esperado == dados.cnpj
    ).first()

    if not licenca or not licenca.cliente_id:
        raise HTTPException(status_code=400, detail="Dados inválidos ou licença não ativada.")
        
    return {"mensagem": "Licença verificada com sucesso!"}
    
@app.post("/recuperar_senha")
def recuperar_senha(dados: schemas.RecuperacaoRequest, db: Session = Depends(get_db)):
    # Criptografa o token recebido para bater com o do banco
    token_criptografado = hashlib.sha256(dados.token_licenca.encode()).hexdigest()
    
    # Procura a licença que bate com o token e o CNPJ informados
    licenca = db.query(models.Licenca).filter(
        models.Licenca.token == token_criptografado,
        models.Licenca.cnpj_esperado == dados.cnpj
    ).first()

    if not licenca or not licenca.cliente_id:
        raise HTTPException(status_code=400, detail="Dados inválidos ou licença não ativada.")

    # Puxa o cliente atrelado a esta licença e atualiza a senha
    cliente = db.query(models.Cliente).filter(models.Cliente.id == licenca.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado no sistema.")

    cliente.senha = dados.nova_senha
    db.commit()
    
    return {"mensagem": "Senha atualizada com sucesso!"}

@app.put("/atualizar_perfil")
def atualizar_perfil(dados: schemas.AtualizarPerfilRequest, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == dados.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    
    cliente.nome_fantasia = dados.nome_fantasia
    cliente.logo_url = dados.logo_url
    db.commit()
    
    return {"mensagem": "Perfil atualizado com sucesso!"}

@app.put("/atualizar_senha")
def atualizar_senha(dados: schemas.AtualizarSenhaRequest, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == dados.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    
    # Verifica se a senha atual está correta antes de mudar
    if cliente.senha != dados.senha_atual:
        raise HTTPException(status_code=400, detail="A senha atual está incorreta.")
        
    cliente.senha = dados.nova_senha
    db.commit()
    
    return {"mensagem": "Senha atualizada com sucesso!"}

@app.get("/categorias/{cliente_id}", response_model=List[schemas.CategoriaResponse])
def listar_categorias(cliente_id: int, db: Session = Depends(get_db)):
    return db.query(models.Categoria).filter(models.Categoria.cliente_id == cliente_id).all()

@app.post("/categorias")
def criar_categoria(dados: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    nova_cat = models.Categoria(cliente_id=dados.cliente_id, nome=dados.nome)
    db.add(nova_cat)
    db.commit()
    return {"mensagem": "Categoria criada com sucesso!"}

@app.get("/motivos/{cliente_id}", response_model=List[schemas.MotivoResponse])
def listar_motivos(cliente_id: int, db: Session = Depends(get_db)):
    return db.query(models.MotivoBaixa).filter(models.MotivoBaixa.cliente_id == cliente_id).all()

@app.post("/motivos")
def criar_motivo(dados: schemas.MotivoCreate, db: Session = Depends(get_db)):
    novo_motivo = models.MotivoBaixa(cliente_id=dados.cliente_id, descricao=dados.descricao, tipo=dados.tipo)
    db.add(novo_motivo)
    db.commit()
    return {"mensagem": "Motivo criado com sucesso!"}

@app.post("/motivo_uso")
def salvar_motivo_uso(dados: schemas.MotivoCreate, db: Session = Depends(get_db)):
    # Procura se o restaurante já tem a palavra de USO cadastrada
    motivo_uso = db.query(models.MotivoBaixa).filter(
        models.MotivoBaixa.cliente_id == dados.cliente_id,
        models.MotivoBaixa.tipo == "USO"
    ).first()
    
    if motivo_uso:
        motivo_uso.descricao = dados.descricao # Só atualiza a palavra
    else:
        novo = models.MotivoBaixa(cliente_id=dados.cliente_id, descricao=dados.descricao, tipo="USO")
        db.add(novo)
        
    db.commit()
    return {"mensagem": "Palavra de uso salva!"}

@app.delete("/categorias/{item_id}")
def deletar_categoria(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Categoria).filter(models.Categoria.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return {"mensagem": "Deletado com sucesso"}

@app.delete("/motivos/{item_id}")
def deletar_motivo(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.MotivoBaixa).filter(models.MotivoBaixa.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return {"mensagem": "Deletado com sucesso"}

@app.put("/atualizar_config_notificacoes")
def atualizar_config_notif(dados: schemas.AtualizarConfigNotifRequest, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == dados.cliente_id).first()
    if cliente:
        cliente.receber_notificacoes = dados.receber_notificacoes
        cliente.limite_global_notificacao = dados.limite_global
        db.commit()
    return {"mensagem": "Configurações globais salvas!"}

@app.put("/atualizar_limite_produto")
def atualizar_limite_produto(dados: schemas.AtualizarLimiteProdutoRequest, db: Session = Depends(get_db)):
    # O estoque_minimo no model Produto é o nosso "limite por produto"
    produto = db.query(models.Produto).filter(models.Produto.id == dados.produto_id, models.Produto.cliente_id == dados.cliente_id).first()
    if produto:
        produto.estoque_minimo = dados.estoque_minimo
        db.commit()
    return {"mensagem": "Limite do produto atualizado!"}

@app.post("/gerar_pagamento_pro")
def gerar_pagamento(dados: schemas.PagamentoPRORequest, db: Session = Depends(get_db)):
    # Mapa de valores e ciclos do Asaas
    planos = {
        "MENSAL": {"ciclo": "MONTHLY", "valor": 95.00},
        "TRIMESTRAL": {"ciclo": "QUARTERLY", "valor": 256.50}, 
        "SEMESTRAL": {"ciclo": "SEMIANNUALLY", "valor": 456.00},
        "ANUAL": {"ciclo": "YEARLY", "valor": 684.00}
    }

    plano_chave = dados.plano.split(" ")[0]
    plano_escolhido = planos.get(plano_chave, planos["MENSAL"])

    # Cria um "Link de Pagamento Recorrente" no Asaas
    payload = {
        "name": f"VegaStock PRO - Plano {plano_chave}",
        "description": "Assinatura do sistema de gestão VegaStock.",
        "chargeType": "RECURRENT", 
        "billingType": "UNDEFINED", 
        "value": plano_escolhido["valor"],
        "cycle": plano_escolhido["ciclo"],
        "endDate": None,
        "dueDateLimitDays": 5,
        "externalReference": str(dados.cliente_id) # <--- ESSA LINHA NOVA (Etiqueta do cliente)
    }

    try:
        response = requests.post(f"{ASAAS_URL}/paymentLinks", json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            dados_asaas = response.json()
            # O Asaas devolve a URL limpa do checkout na chave 'url'
            return {"link_pagamento": dados_asaas["url"]}
        else:
            raise HTTPException(status_code=400, detail=f"Erro no Asaas: {response.text}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/forcar_pro/{cliente_id}")
def forcar_pro(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if cliente:
        cliente.status_assinatura = "PRO"
        db.commit()
        return {"status": "SUCESSO", "mensagem": f"O cliente {cliente.nome_fantasia} agora é PRO!"}
    return {"status": "ERRO", "mensagem": "Cliente não encontrado"}
    
@app.post("/webhook_asaas")
async def webhook_asaas(request: Request, db: Session = Depends(get_db)):
    # O Asaas manda um JSON avisando o que aconteceu
    payload = await request.json()
    
    # Verifica se a fofoca é sobre um pagamento confirmado/recebido
    evento = payload.get("event")
    if evento in ["PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"]:
        
        pagamento = payload.get("payment", {})
        cliente_id_str = pagamento.get("externalReference") # Pega a etiqueta que mandamos
        
        if cliente_id_str:
            cliente_id = int(cliente_id_str)
            
            # Atualiza o banco do VegaStock! O cliente agora é PRO.
            cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
            if cliente:
                cliente.status_assinatura = "PRO"
                db.commit()

    return {"status": "recebido"}

@app.post("/produtos")
def criar_produto(dados: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    novo_produto = models.Produto(
        cliente_id=dados.cliente_id,
        nome=dados.nome,
        categoria_id=dados.categoria_id,
        unidade_medida=dados.unidade_medida,
        estoque_minimo=dados.estoque_minimo
    )
    db.add(novo_produto)
    db.commit()
    return {"mensagem": "Produto criado com sucesso!"}

@app.delete("/produtos/{produto_id}")
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if produto:
        db.delete(produto)
        db.commit()
    return {"mensagem": "Produto deletado com sucesso!"}

# ==========================================
# ROTAS: UNIDADES DE MEDIDA
# ==========================================
@app.get("/unidades/{cliente_id}", response_model=List[schemas.UnidadeResponse])
def listar_unidades(cliente_id: int, db: Session = Depends(get_db)):
    unidades = db.query(models.UnidadeMedida).filter(models.UnidadeMedida.cliente_id == cliente_id).all()
    
    # Semente Automática: Se o cliente não tem unidades, cria as padrões agora.
    if not unidades:
        padroes = ["kg", "litro", "unidade", "caixa", "maço", "gramas", "ml"]
        for p in padroes:
            db.add(models.UnidadeMedida(cliente_id=cliente_id, nome=p))
        db.commit()
        unidades = db.query(models.UnidadeMedida).filter(models.UnidadeMedida.cliente_id == cliente_id).all()
        
    return unidades

@app.post("/unidades")
def criar_unidade(dados: schemas.UnidadeCreate, db: Session = Depends(get_db)):
    # Transforma tudo em minúsculo para padronizar (anti-idiota)
    nome_formatado = dados.nome.strip().lower()
    
    # Verifica se já existe para este cliente
    existe = db.query(models.UnidadeMedida).filter(
        models.UnidadeMedida.cliente_id == dados.cliente_id,
        models.UnidadeMedida.nome == nome_formatado
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="Esta unidade já está cadastrada.")
        
    nova_unidade = models.UnidadeMedida(cliente_id=dados.cliente_id, nome=nome_formatado)
    db.add(nova_unidade)
    db.commit()
    return {"mensagem": "Unidade criada com sucesso!"}

@app.put("/unidades/{item_id}")
def editar_unidade(item_id: int, dados: schemas.UnidadeUpdate, db: Session = Depends(get_db)):
    item = db.query(models.UnidadeMedida).filter(models.UnidadeMedida.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
        
    item.nome = dados.nome.strip().lower()
    db.commit()
    return {"mensagem": "Unidade editada com sucesso!"}

@app.delete("/unidades/{item_id}")
def deletar_unidade(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.UnidadeMedida).filter(models.UnidadeMedida.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return {"mensagem": "Unidade deletada com sucesso!"}