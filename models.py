from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class ImportacaoCatalogo(Base):
    __tablename__ = "importacoes_catalogo"
    chave = Column(String, primary_key=True)

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    
    agendamentos = relationship("Agendamento", back_populates="usuario")

class RecuperacaoSenha(Base):
    __tablename__ = "recuperacoes_senha"
    token_hash = Column(String(64), primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    assinatura_senha = Column(String(64), nullable=False)
    expira_em = Column(DateTime, nullable=False)
    usado_em = Column(DateTime, nullable=True)

class LimiteRecuperacao(Base):
    __tablename__ = "limites_recuperacao"
    chave = Column(String(64), primary_key=True)
    inicio = Column(DateTime, nullable=False)
    tentativas = Column(Integer, nullable=False)

class Quadra(Base):
    __tablename__ = "quadras"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    localizacao = Column(String)
    tipo = Column(String)
    imagem_url = Column(String, nullable=True) # <-- Coluna para a URL da foto
    
    agendamentos = relationship("Agendamento", back_populates="quadra")
    comentarios = relationship("ComentarioQuadra", back_populates="quadra", cascade="all, delete-orphan")

class ComentarioQuadra(Base):
    __tablename__ = "comentarios_quadras"
    id = Column(Integer, primary_key=True, index=True)
    quadra_id = Column(Integer, ForeignKey("quadras.id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    texto = Column(String(1000), nullable=False)
    criado_em = Column(DateTime, nullable=False, default=datetime.now)
    quadra = relationship("Quadra", back_populates="comentarios")
    usuario = relationship("Usuario")

class Agendamento(Base):
    __tablename__ = "agendamentos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    quadra_id = Column(Integer, ForeignKey("quadras.id"))
    data_hora_inicio = Column(DateTime)
    data_hora_fim = Column(DateTime)
    
    usuario = relationship("Usuario", back_populates="agendamentos")
    quadra = relationship("Quadra", back_populates="agendamentos")
