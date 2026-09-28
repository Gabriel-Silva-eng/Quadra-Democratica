from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class UsuarioBase(BaseModel):
    nome: str
    email: str

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(UsuarioBase):
    id: int
    class Config:
        from_attributes = True

class QuadraBase(BaseModel):
    nome: str
    localizacao: str
    tipo: str
    imagem_url: Optional[str] = None # <-- Campo opcional na API

class QuadraCreate(QuadraBase):
    pass

class QuadraResponse(QuadraBase):
    id: int
    class Config:
        from_attributes = True

class AgendamentoBase(BaseModel):
    quadra_id: int
    data_hora_inicio: datetime
    data_hora_fim: datetime

class AgendamentoCreate(AgendamentoBase):
    pass

class AgendamentoResponse(AgendamentoBase):
    id: int
    usuario_id: int
    class Config:
        from_attributes = True