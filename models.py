from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from datetime import datetime
from database import Base

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nome_fantasia = Column(String, index=True)
    cnpj = Column(String, unique=True, index=True)
    logo_url = Column(String, nullable=True)
    status_assinatura = Column(String, default="Ativo")
    receber_notificacoes = Column(Boolean, default=True) # Gatilho para a aba de Configurações
    limite_global_notificacao = Column(Float, default=5.0) # Valor padrão global
    validade_pro = Column(DateTime, nullable=True) # Data em que o acesso PRO expira

class CategoriaProduto(Base):
    __tablename__ = "categorias_produto"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    nome = Column(String)

class MotivoBaixa(Base):
    __tablename__ = "motivos_baixa"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    descricao = Column(String)
    tipo = Column(String)  # "POSITIVO" (Venda) ou "NEGATIVO" (Desperdício)

class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    motivo_baixa_id = Column(Integer, ForeignKey("motivos_baixa.id"), nullable=True) # Nullable porque nem toda movimentação precisa de motivo (ex: Entrada por compra)
    tipo_movimento = Column(String)  # "ENTRADA" ou "SAIDA"
    quantidade = Column(Float)
    custo_unitario = Column(Float, nullable=True) # Quanto ele pagou na hora da Entrada
    data_hora = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, nullable=True)  # Nullable até termos o módulo de RH/Login de Staff
    
class Licenca(Base):
    __tablename__ = "licencas"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(12), unique=True, index=True) 
    usada = Column(Boolean, default=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True) 
    cnpj_esperado = Column(String, index=True) # Trava o token a este CNPJ
    data_expiracao = Column(DateTime) # Janela de 48h

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id")) # O usuário fica trancado dentro do bloco do restaurante dele
    login = Column(String, unique=True, index=True)
    senha = Column(String) 
    nivel_acesso = Column(String, default="Admin") # Para futuramente separar o Dono do Almoxarife
    cnpj_esperado = Column(String, index=True) # Trava o token a este CNPJ
    data_expiracao = Column(DateTime) # Janela de 48h
    permissoes = Column(String, default="dashboard") # Dashboard é o acesso mínimo
    cargo = Column(String, nullable=True) # Ex: Estoquista, Gerente
    
class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id")) # Cada restaurante tem suas próprias categorias
    nome = Column(String, index=True)

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    nome = Column(String, index=True)
    unidade_medida = Column(String) # Kg, Litro, Unidade, etc.
    custo_medio = Column(Float, default=0.0)
    estoque_minimo = Column(Float, default=0.0)
    quantidade_atual = Column(Float, default=0.0)
    codigo_barras = Column(String, index=True, nullable=True)

class UnidadeMedida(Base):
    __tablename__ = "unidades_medida"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    nome = Column(String, index=True)