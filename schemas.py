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
    unidade_medida: str
    quantidade_atual: float

    class Config:
        from_attributes = True

# Schema que o PySide vai ENVIAR para dar a baixa
class MovimentacaoCreate(BaseModel):
    cliente_id: int
    produto_id: int
    motivo_baixa_id: int
    quantidade: float
    
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