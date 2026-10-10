from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from datetime import datetime

class UsuarioBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value):
        return str(value).lower()

class UsuarioCreate(UsuarioBase):
    senha: str = Field(min_length=8)

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("A senha deve ter no máximo 72 bytes.")
        return value

class UsuarioResponse(UsuarioBase):
    id: int
    class Config:
        from_attributes = True

class QuadraBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    localizacao: str = Field(min_length=1, max_length=300)
    tipo: str = Field(min_length=1, max_length=80)
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
    @model_validator(mode="after")
    def validar_periodo(self):
        if self.data_hora_inicio.tzinfo or self.data_hora_fim.tzinfo:
            raise ValueError("Use o horário local da quadra, sem fuso horário.")
        minutos = (self.data_hora_fim - self.data_hora_inicio).total_seconds() / 60
        if not 30 <= minutos <= 120:
            raise ValueError("A reserva deve durar entre 30 minutos e 2 horas.")
        if self.data_hora_inicio < datetime.now():
            raise ValueError("A reserva deve ser no futuro.")
        return self

class AgendamentoResponse(AgendamentoBase):
    id: int
    usuario_id: int
    class Config:
        from_attributes = True
