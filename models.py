from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    
    agendamentos = relationship("Agendamento", back_populates="usuario")

class Quadra(Base):
    __tablename__ = "quadras"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    localizacao = Column(String)
    tipo = Column(String)
    imagem_url = Column(String, nullable=True) # <-- Coluna para a URL da foto
    
    agendamentos = relationship("Agendamento", back_populates="quadra")

class Agendamento(Base):
    __tablename__ = "agendamentos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    quadra_id = Column(Integer, ForeignKey("quadras.id"))
    data_hora_inicio = Column(DateTime)
    data_hora_fim = Column(DateTime)
    
    usuario = relationship("Usuario", back_populates="agendamentos")
    quadra = relationship("Quadra", back_populates="agendamentos")