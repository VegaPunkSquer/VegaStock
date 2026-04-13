from datetime import timedelta, datetime
from collections import defaultdict
from sqlalchemy import desc
from fastapi import FastAPI, Request, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import SessionLocal
import models
import schemas
import hashlib
import requests
import os
from dotenv import load_dotenv

app = FastAPI(title="SaaS Restaurante - Estoque API")

# Carrega o cofre invisível (.env)
load_dotenv() 

# Puxa a chave de dentro do cofre
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")
ASAAS_WEBHOOK_TOKEN = os.getenv("ASAAS_WEBHOOK_TOKEN")

# Mantém a URL (Quando for pra valer, é só apagar a palavra 'sandbox.' daqui)
ASAAS_URL = "https://api.asaas.com/v3"

# Mantém os Headers porque a requisição lá embaixo precisa deles
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
# ==========================================
# ROTAS: OPERAÇÃO DE ESTOQUE
# ==========================================
@app.post("/movimentacao")
def registrar_movimentacao(mov: schemas.MovimentacaoCreate, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == mov.produto_id, models.Produto.cliente_id == mov.cliente_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    nova_movimentacao = models.MovimentacaoEstoque(
        cliente_id=mov.cliente_id,
        produto_id=mov.produto_id,
        tipo_movimento=mov.tipo_movimento,
        quantidade=mov.quantidade
    )

    if mov.tipo_movimento == "ENTRADA":
        if mov.custo_unitario is None:
            raise HTTPException(status_code=400, detail="Entrada exige o preenchimento do custo unitário.")
        
        # O Motor da Matemática: Calcula o Custo Médio Ponderado
        estoque_total_futuro = produto.quantidade_atual + mov.quantidade
        if estoque_total_futuro > 0:
            custo_antigo_total = produto.quantidade_atual * produto.custo_medio
            custo_novo_total = mov.quantidade * mov.custo_unitario
            produto.custo_medio = (custo_antigo_total + custo_novo_total) / estoque_total_futuro
        
        produto.quantidade_atual += mov.quantidade
        nova_movimentacao.custo_unitario = mov.custo_unitario

    elif mov.tipo_movimento == "SAIDA":
        if mov.motivo_baixa_id is None:
            raise HTTPException(status_code=400, detail="Saída exige a seleção de um motivo.")
        if produto.quantidade_atual < mov.quantidade:
            raise HTTPException(status_code=400, detail="Estoque insuficiente para esta saída.")
        
        produto.quantidade_atual -= mov.quantidade
        nova_movimentacao.motivo_baixa_id = mov.motivo_baixa_id

    db.add(nova_movimentacao)
    db.commit()
    return {"status": "sucesso", "novo_saldo": produto.quantidade_atual, "novo_custo": produto.custo_medio}

@app.get("/movimentacoes/{cliente_id}")
def listar_movimentacoes(cliente_id: int, dias: int = 30, db: Session = Depends(get_db)):
    """Puxa o histórico forçando a ordem correta e o motivo exato."""
    # Data de corte ajustada para o fuso correto do Brasil (UTC-3)
    data_corte = datetime.utcnow() - timedelta(hours=3, days=dias)
    
    # O desc() força a trazer o ID mais novo primeiro (ordem cronológica perfeita)
    movimentacoes = db.query(models.MovimentacaoEstoque).filter(
        models.MovimentacaoEstoque.cliente_id == cliente_id,
        models.MovimentacaoEstoque.data_hora >= data_corte
    ).order_by(desc(models.MovimentacaoEstoque.id)).all()
    
    movimentacoes.sort(key=lambda x: x.id, reverse=True)

    resultado = []
    for m in movimentacoes:
        # Puxa o nome do produto
        produto = db.query(models.Produto).filter(models.Produto.id == m.produto_id).first()
        nome_produto = produto.nome if produto else "Deletado"
        unidade = produto.unidade_medida if produto else ""

        # Puxa o nome EXATO do motivo e trava para evitar o erro do "Nova Entrada"
        nome_motivo = ""
        if m.motivo_baixa_id and m.tipo_movimento.lower() == "saida":
            motivo = db.query(models.MotivoBaixa).filter(models.MotivoBaixa.id == m.motivo_baixa_id).first()
            nome_motivo = motivo.descricao if motivo else ""

        resultado.append({
            "id": m.id,
            "data": m.data_hora.strftime("%d/%m/%Y\n%H:%M"),
            "tipo": m.tipo_movimento.upper(),
            "produto": nome_produto,
            "quantidade": m.quantidade,
            "unidade": unidade,
            "custo": m.custo_unitario,
            "motivo": nome_motivo
        })
    return resultado

# 4. Endpoint: Relatório de Desperdício (A isca de vendas)
@app.get("/relatorios/desperdicio/{cliente_id}")
def relatorio_desperdicio(cliente_id: int, dias: int = 30, categoria_id: int = None, motivo_id: int = None, db: Session = Depends(get_db)):
    # 1. Ajuste do Fuso Horário de João Pessoa (UTC-3)
    hoje_brasil = datetime.utcnow() - timedelta(hours=3)
    
    # Se for "Hoje" (dias=1), o corte é exatamente a meia-noite de hoje
    if dias == 1:
        data_corte = hoje_brasil.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        data_corte = hoje_brasil - timedelta(days=dias)

    # 2. Busca apenas as SAÍDAS
    query = db.query(models.MovimentacaoEstoque).filter(
        models.MovimentacaoEstoque.cliente_id == cliente_id,
        models.MovimentacaoEstoque.tipo_movimento == "SAIDA",
        models.MovimentacaoEstoque.data_hora >= data_corte
    )
    if motivo_id:
        query = query.filter(models.MovimentacaoEstoque.motivo_baixa_id == motivo_id)
        
    movimentacoes = query.all()

    total_prejuizo = 0.0
    produtos_perdidos = defaultdict(float)
    motivos_perdidos = defaultdict(float)
    tabela = []

    for m in movimentacoes:
        # Só calcula se o motivo existir e se o custo existir (agora vai existir graças ao código novo)
        custo = float(m.custo_unitario) if m.custo_unitario else 0.0
        prejuizo_linha = custo * float(m.quantidade)
        
        produto = db.query(models.Produto).filter(models.Produto.id == m.produto_id).first()
        # Aplica o filtro de categoria se o usuário selecionou na tela
        if categoria_id and (not produto or produto.categoria_id != categoria_id):
            continue

        nome_produto = produto.nome if produto else "Deletado"
        cat = db.query(models.Categoria).filter(models.Categoria.id == produto.categoria_id).first() if produto and produto.categoria_id else None
        nome_cat = cat.nome if cat else "Sem Categoria"

        motivo = db.query(models.MotivoBaixa).filter(models.MotivoBaixa.id == m.motivo_baixa_id).first() if m.motivo_baixa_id else None
        nome_motivo = motivo.descricao if motivo else "Sem Motivo"

        # Soma nos KPIs
        total_prejuizo += prejuizo_linha
        produtos_perdidos[nome_produto] += prejuizo_linha
        motivos_perdidos[nome_motivo] += prejuizo_linha

        # Adiciona na tabela forçando as casas decimais
        tabela.append({
            "produto": nome_produto,
            "categoria": nome_cat,
            "quantidade_perdida": m.quantidade,
            "unidade": produto.unidade_medida if produto else "",
            "motivo": nome_motivo,
            "custo_total_perdido_rs": prejuizo_linha,
            "data": m.data_hora.strftime("%d/%m/%Y")
        })

    # Descobre o maior vilão (Produto e Motivo)
    top_produto = max(produtos_perdidos, key=produtos_perdidos.get) if produtos_perdidos else "Nenhum"
    top_produto_valor = produtos_perdidos[top_produto] if produtos_perdidos else 0.0

    top_motivo = max(motivos_perdidos, key=motivos_perdidos.get) if motivos_perdidos else "Nenhum"
    top_motivo_valor = motivos_perdidos[top_motivo] if motivos_perdidos else 0.0

    return {
        "kpis": {
            "total_prejuizo": total_prejuizo,
            "top_produto": top_produto,
            "top_produto_valor": top_produto_valor,
            "top_motivo": top_motivo,
            "top_motivo_valor": top_motivo_valor
        },
        "tabela": tabela
    }

# Função interna para gerar a criptografia (Hash)
def gerar_hash(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()

@app.post("/cadastrar")
def cadastrar_restaurante(dados: schemas.CadastroRequest, db: Session = Depends(get_db)):
    # 1. Validar a Licença (Lê direto o que o cliente digitou)
    licenca = db.query(models.Licenca).filter(models.Licenca.token == dados.token_licenca, models.Licenca.usada == False).first()
    
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
        "usuario_id": usuario.id,              # <-- NOVO: ID do funcionário logado
        "nome_fantasia": cliente.nome_fantasia,
        "login_usuario": usuario.login,
        "nivel_acesso": getattr(usuario, 'nivel_acesso', 'normal'), # Mantido (com getattr pra não quebrar se o banco ainda não tiver)
        "cargo": getattr(usuario, 'cargo', 'Admin'),                # <-- NOVO: Cargo
        "logo_url": cliente.logo_url,          # <-- MANTIDO: O que salva a sua imagem
        "status_assinatura": cliente.status_assinatura, 
        "limite_global": cliente.limite_global_notificacao,
        "permissoes": usuario.permissoes.split(",") if getattr(usuario, 'permissoes', None) else [] # <-- NOVO: Lista de travas
    }
    
@app.post("/verificar_licenca")
def verificar_licenca(dados: schemas.VerificarLicencaRequest, db: Session = Depends(get_db)):
    licenca = db.query(models.Licenca).filter(
        models.Licenca.token == dados.token_licenca,
        models.Licenca.cnpj_esperado == dados.cnpj
    ).first()

    if not licenca or not licenca.cliente_id:
        raise HTTPException(status_code=400, detail="Dados inválidos ou licença não ativada.")
        
    return {"mensagem": "Licença verificada com sucesso!"}
    
@app.post("/recuperar_senha")
def recuperar_senha(dados: schemas.RecuperacaoRequest, db: Session = Depends(get_db)):
    # Procura a licença que bate com o token e o CNPJ informados
    licenca = db.query(models.Licenca).filter(
        models.Licenca.token == dados.token_licenca,
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

# ==========================================
# ROTA: DASHBOARD (RESUMO GERAL)
# ==========================================
@app.get("/dashboard/resumo/{cliente_id}")
def resumo_dashboard(cliente_id: int, db: Session = Depends(get_db)):
    # 1. Busca todos os produtos do cliente
    produtos = db.query(models.Produto).filter(models.Produto.cliente_id == cliente_id).all()
    
    patrimonio_total = 0.0
    itens_abaixo_minimo = []
    total_itens_estoque = len(produtos)

    for p in produtos:
        # Soma o valor total parado (Qtd Atual * Custo Médio)
        valor_produto = p.quantidade_atual * p.custo_medio
        patrimonio_total += valor_produto
        
        # Verifica Alerta de Estoque Mínimo
        if p.quantidade_atual < p.estoque_minimo:
            itens_abaixo_minimo.append({
                "id": p.id,
                "nome": p.nome,
                "qtd_atual": p.quantidade_atual,
                "qtd_minima": p.estoque_minimo,
                "unidade": p.unidade_medida
            })

    # 2. Busca movimentações de HOJE agrupadas pela unidade de medida do produto
    hoje_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Faz uma "costura" (JOIN) com a tabela de Produtos para descobrir a unidade de medida na mesma viagem
    movs_hoje = db.query(
        models.MovimentacaoEstoque.tipo_movimento,
        models.MovimentacaoEstoque.quantidade,
        models.Produto.unidade_medida
    ).join(
        models.Produto, models.MovimentacaoEstoque.produto_id == models.Produto.id
    ).filter(
        models.MovimentacaoEstoque.cliente_id == cliente_id,
        models.MovimentacaoEstoque.data_hora >= hoje_inicio
    ).all()

    # Cria os potinhos vazios
    dic_entradas = {}
    dic_saidas = {}

    # Separa a bagunça de hoje, somando cada um no seu potinho correto
    for tipo, qtd, unidade in movs_hoje:
        un = unidade if unidade else "un" # Se o produto estiver sem unidade, assume 'un'
        if tipo == "ENTRADA":
            dic_entradas[un] = dic_entradas.get(un, 0) + qtd
        elif tipo == "SAIDA":
            dic_saidas[un] = dic_saidas.get(un, 0) + qtd

    # Converte os potinhos num texto limpo. Ex: "30.0 kg, 12.0 un"
    texto_entradas = ", ".join([f"{v} {k}" for k, v in dic_entradas.items()]) if dic_entradas else "Nenhuma"
    texto_saidas = ", ".join([f"{v} {k}" for k, v in dic_saidas.items()]) if dic_saidas else "Nenhuma"

    return {
        "patrimonio_rs": round(patrimonio_total, 2),
        "total_produtos": total_itens_estoque,
        "alertas_criticos_qtd": len(itens_abaixo_minimo),
        "lista_compras": itens_abaixo_minimo,
        "movimento_hoje": {
            "entradas": texto_entradas,
            "saidas": texto_saidas
        }
    }
    
# ==========================================
# ROTA: GESTÃO DE EQUIPE (ADMIN ONLY)
# ==========================================

# 1. Listar Equipe
@app.get("/equipe/{cliente_id}")
def listar_equipe(cliente_id: int, db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).filter(models.Usuario.cliente_id == cliente_id).all()
    return [{
        "id": u.id, 
        "login": u.login, 
        "cargo": u.cargo, 
        "permissoes": u.permissoes.split(",") if u.permissoes else []
    } for u in usuarios]

# 2. Adicionar/Editar Funcionário
@app.post("/equipe")
def salvar_funcionario(dados: dict, db: Session = Depends(get_db)):
    # Se tiver ID, edita. Se não, cria novo.
    user_id = dados.get("id")
    if user_id:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    else:
        usuario = models.Usuario(cliente_id=dados["cliente_id"])
        db.add(usuario)
    
    usuario.login = dados["login"]
    if dados.get("senha"): # Só muda a senha se enviar uma nova
        usuario.senha = dados["senha"]
    usuario.cargo = dados["cargo"]
    # Transforma a lista do front ['estoque', 'relatorios'] em string "estoque,relatorios"
    usuario.permissoes = ",".join(dados["permissoes"])
    
    db.commit()
    return {"status": "sucesso"}

# 3. Excluir Funcionário
@app.delete("/equipe/{usuario_id}")
def excluir_funcionario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if usuario:
        db.delete(usuario)
        db.commit()
    return {"status": "removido"}

# ==========================================
# ROTA: ATUALIZAR CONTA DO FUNCIONÁRIO
# ==========================================
@app.put("/atualizar_conta_funcionario")
def atualizar_conta_funcionario(dados: dict, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == dados["usuario_id"]).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Atualiza o login (se enviou um novo)
    if dados.get("novo_login"):
        # Verifica se o novo login já existe pra outra pessoa
        existe = db.query(models.Usuario).filter(models.Usuario.login == dados["novo_login"], models.Usuario.id != dados["usuario_id"]).first()
        if existe:
            raise HTTPException(status_code=400, detail="Este login já está em uso.")
        usuario.login = dados["novo_login"]
        
    # Atualiza a senha (se enviou uma nova)
    if dados.get("nova_senha"):
        usuario.senha = gerar_hash(dados["nova_senha"])
        
    db.commit()
    return {"mensagem": "Conta atualizada com sucesso!"}

# ==========================================
# ROTA: RADAR DE PAGAMENTO (Para o App)
# ==========================================
@app.get("/status_assinatura/{cliente_id}")
def checar_status_assinatura(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if cliente:
        return {"status": cliente.status_assinatura}
    return {"status": "Normal"}

# ==========================================
# ROTA: WEBHOOK DO ASAAS (Recebe a confirmação de pagamento)
# ==========================================
@app.post("/webhook/asaas")
async def asaas_webhook(request: Request, asaas_access_token: str = Header(None), db: Session = Depends(get_db)):
    
    # 1. Barreira de Segurança: Verifica se foi o Asaas mesmo que mandou
    if asaas_access_token != ASAAS_WEBHOOK_TOKEN:
        raise HTTPException(status_code=403, detail="Token de Webhook inválido. Acesso Negado.")

    # 2. Lê a mensagem JSON que o Asaas mandou
    payload = await request.json()
    evento = payload.get("event")

    # 3. Se for um evento de dinheiro na conta
    if evento in ["PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"]:
        pagamento = payload.get("payment", {})
        
        # Pega a identificação de qual cliente pagou (vem do externalReference)
        cliente_id_str = pagamento.get("externalReference")

        if cliente_id_str:
            cliente = db.query(models.Cliente).filter(models.Cliente.id == int(cliente_id_str)).first()
            if cliente:
                # A MÁGICA ACONTECE AQUI: Carimba o banco de dados como PRO
                cliente.status_assinatura = "PRO"
                db.commit()

    # O Asaas exige que a gente responda algo para ele saber que a mensagem chegou, senão ele fica reenviando
    return {"status": "recebido"}

# ==========================================
# ROTAS DO LEITOR DE CÓDIGO DE BARRAS (MOBILE)
# ==========================================

@app.put("/vincular_codigo")
def vincular_codigo(dados: dict, db: Session = Depends(get_db)):
    """O Batismo Blindado"""
    produto_id = dados.get("produto_id")
    # Força a ser texto e corta qualquer espaço invisível ou quebra de linha!
    codigo = str(dados.get("codigo_barras")).strip() 
    cliente_id = dados.get("cliente_id")
    
    produto = db.query(models.Produto).filter(
        models.Produto.id == produto_id,
        models.Produto.cliente_id == cliente_id
    ).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
        
    produto.codigo_barras = codigo
    db.commit()
    db.refresh(produto) # Força o banco a devolver a prova de que salvou
    return {"mensagem": "Salvo!", "prova_do_crime": produto.codigo_barras}

@app.get("/produtos_mobile/{cliente_id}")
def listar_produtos_mobile(cliente_id: int, db: Session = Depends(get_db)):
    """Puxa a lista e agora MOSTRA se tem código salvo ou não."""
    produtos = db.query(models.Produto).filter(models.Produto.cliente_id == cliente_id).all()
    # Adicionamos a gaveta do codigo_barras aqui pra gente auditar
    return [{"id": p.id, "nome": p.nome, "unidade_medida": p.unidade_medida, "codigo_barras": p.codigo_barras} for p in produtos]

@app.get("/produto_por_codigo/{cliente_id}/{codigo}")
def buscar_produto_por_codigo(cliente_id: int, codigo: str, db: Session = Depends(get_db)):
    """O Detetive Blindado"""
    codigo_limpo = codigo.strip() # Limpa a sujeira aqui também
    produto = db.query(models.Produto).filter(
        models.Produto.cliente_id == cliente_id,
        models.Produto.codigo_barras == codigo_limpo
    ).first()

    if not produto:
        raise HTTPException(status_code=404, detail="Código não reconhecido.")
        
    return {
        "id": produto.id,
        "nome": produto.nome,
        "unidade_medida": produto.unidade_medida
    }

@app.get("/motivos_mobile/{cliente_id}")
def listar_motivos_mobile(cliente_id: int, db: Session = Depends(get_db)):
    """Envia a lista de motivos cadastrados para o celular."""
    motivos = db.query(models.MotivoBaixa).filter(models.MotivoBaixa.cliente_id == cliente_id).all()
    return [{"id": m.id, "descricao": m.descricao} for m in motivos]

@app.post("/movimentar_mobile")
def movimentar_mobile(dados: dict, db: Session = Depends(get_db)):
    produto_id = dados.get("produto_id")
    cliente_id = dados.get("cliente_id")
    
    # 1. Padroniza para evitar erro no Dashboard
    tipo = str(dados.get("tipo_movimento", "")).upper()
    qtd_bruta = str(dados.get("quantidade", "0")).replace(",", ".")
    qtd = float(qtd_bruta) if qtd_bruta.strip() != "" else 0.0
    custo_bruto = str(dados.get("custo_unitario", "0")).replace(",", ".")
    custo_digitado = float(custo_bruto) if custo_bruto.strip() != "" else 0.0
    motivo_id = dados.get("motivo_baixa_id")

    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    
    # 2. Blindagem contra o "vazio" (NULL) do Catálogo
    q_atual = produto.quantidade_atual if produto.quantidade_atual is not None else 0.0
    c_medio = produto.custo_medio if produto.custo_medio is not None else 0.0

    if tipo == "ENTRADA":
        produto.quantidade_atual = q_atual + qtd
        produto.custo_medio = float(custo_digitado)
        custo_final = float(custo_digitado)
    else: # SAIDA
        produto.quantidade_atual = q_atual - qtd
        custo_final = c_medio

    db.add(produto) # Salva a nova realidade do produto

    # 3. Registra o histórico
    nova_mov = models.MovimentacaoEstoque(
        cliente_id=cliente_id,
        produto_id=produto_id,
        tipo_movimento=tipo,
        quantidade=qtd,
        custo_unitario=custo_final,
        motivo_baixa_id=motivo_id if tipo == "SAIDA" else None,
        usuario_id=1,
        operador_nome=dados.get("operador_nome", "Desconhecido")
    )
    db.add(nova_mov)
    db.commit()
    return {"mensagem": "Movimentação registrada!"}

@app.put("/produtos/{produto_id}")
async def editar_produto(produto_id: int, request: Request, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Abre o "pacote" JSON na marra
    dados = await request.json()

    # Atualiza SÓ o que veio da tela
    produto.nome = dados.get("nome", produto.nome)
    produto.unidade_medida = dados.get("unidade_medida", produto.unidade_medida)

    db.commit()
    return {"mensagem": "Produto atualizado com sucesso!"}

@app.post("/validar_pin")
def validar_pin(dados: dict, db: Session = Depends(get_db)):
    cliente_id = dados.get("cliente_id")
    pin_digitado = str(dados.get("pin"))

    # Procura se existe alguém com esse PIN naquele restaurante
    operador = db.query(models.OperadorTurno).filter(
        models.OperadorTurno.cliente_id == cliente_id,
        models.OperadorTurno.pin == pin_digitado
    ).first()

    if operador:
        return {"sucesso": True, "nome": operador.nome}
    else:
        raise HTTPException(status_code=401, detail="PIN incorreto ou não encontrado.")