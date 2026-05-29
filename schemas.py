from pydantic import BaseModel
from typing import Optional

# Schema para o retorno das configurações White-Label
class ClienteConfig(BaseModel):
    nome_fantasia: str
    logo_url: Optional[str] = None
    cor_primaria: Optional[str] = None

    class Config:
        from_attributes = True

# Schema para listar o estoque no tabelão do PySide
class ProdutoResponse(BaseModel):
    id: int
    nome: str
    categoria_id: Optional[int] = None
    unidade_medida: str
    estoque_minimo: float
    quantidade_atual: float

    class Config:
        from_attributes = True

class ProdutoCreate(BaseModel):
    cliente_id: int
    nome: str
    categoria_id: int
    unidade_medida: str
    estoque_minimo: float

# Schema que o PySide vai ENVIAR para dar a baixa
class MovimentacaoCreate(BaseModel):
    cliente_id: int
    produto_id: int
    tipo_movimento: str  # "ENTRADA" ou "SAIDA"
    motivo_baixa_id: Optional[int] = None #Só pra saída
    quantidade: float
    custo_unitario: Optional[float] = None # Quanto ele pagou na hora da Entrada
class CadastroRequest(BaseModel):
    token_licenca: str
    nome_fantasia: str
    cnpj: str
    login: str
    senha: str
    logo_url: str = ""  # NOVA LINHA: Recebe o caminho absoluto da imagem

class LoginRequest(BaseModel):
    login: str
    senha: str
    
class RecuperacaoRequest(BaseModel):
    cnpj: str
    token_licenca: str
    nova_senha: str
    
class VerificarLicencaRequest(BaseModel):
    cnpj: str
    token_licenca: str
    
class AtualizarPerfilRequest(BaseModel):
    cliente_id: int
    nome_fantasia: str
    logo_url: str

class AtualizarSenhaRequest(BaseModel):
    cliente_id: int
    senha_atual: str
    nova_senha: str
    
class CategoriaCreate(BaseModel):
    cliente_id: int
    nome: str

class CategoriaResponse(BaseModel):
    id: int
    nome: str
    class Config:
        from_attributes = True

class MotivoCreate(BaseModel):
    cliente_id: int
    descricao: str
    tipo: str

class MotivoResponse(BaseModel):
    id: int
    descricao: str
    tipo: str
    class Config:
        from_attributes = True
        
class AtualizarConfigNotifRequest(BaseModel):
    cliente_id: int
    receber_notificacoes: bool
    limite_global: float

class AtualizarLimiteProdutoRequest(BaseModel):
    produto_id: int
    cliente_id: int
    estoque_minimo: float
    
class PagamentoPRORequest(BaseModel):
    cliente_id: int
    plano: str
    
class UnidadeCreate(BaseModel):
    cliente_id: int
    nome: str

class UnidadeUpdate(BaseModel):
    nome: str

class UnidadeResponse(BaseModel):
    id: int
    nome: str
    class Config:
        from_attributes = True
        
class WhitelistCreate(BaseModel):
    cnpj: str
    plano: str
    data_fim: str