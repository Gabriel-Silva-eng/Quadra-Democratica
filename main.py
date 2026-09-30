from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from typing import List
from fastapi import Response, status, HTTPException

import models
import schemas
from database import engine, SessionLocal

# Cria as tabelas automaticamente se não existirem
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Quadra Democrática",
    description="Backend seguro para agendamento de quadras públicas.",
    version="1.0.0"
)

# --- CONFIGURAÇÃO DE CORS (Crucial para o Frontend conseguir conversar com a API) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, trocaremos isso pelo domínio do seu site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÕES DE SEGURANÇA (JWT e Bcrypt) ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "super_secreta_chave_de_teste_mude_depois"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def criar_token_acesso(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- DEPENDÊNCIAS DE BANCO DE DADOS E AUTENTICAÇÃO ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# O "Segurança da Balada": Intercepta a requisição e valida o token
def get_usuario_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario is None:
        raise credentials_exception
    return usuario

# --- ROTAS DA API ---

@app.get("/")
def read_root():
    return {"status": "ok", "mensagem": "Servidor operante."}

# 1. Usuários e Login
@app.post("/usuarios/", response_model=schemas.UsuarioResponse)
def criar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="Email já cadastrado na plataforma.")
    
    hashed_password = get_password_hash(usuario.senha)
    novo_usuario = models.Usuario(nome=usuario.nome, email=usuario.email, senha_hash=hashed_password)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()
    if not usuario or not pwd_context.verify(form_data.password, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    
    access_token = criar_token_acesso(data={"sub": usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}

# 2. Quadras
@app.post("/quadras/", response_model=schemas.QuadraResponse)
def criar_quadra(quadra: schemas.QuadraCreate, db: Session = Depends(get_db), usuario_atual: models.Usuario = Depends(get_usuario_atual)):
    nova_quadra = models.Quadra(**quadra.model_dump())
    db.add(nova_quadra)
    db.commit()
    db.refresh(nova_quadra)
    return nova_quadra

@app.get("/quadras/", response_model=List[schemas.QuadraResponse])
def listar_quadras(db: Session = Depends(get_db)):
    return db.query(models.Quadra).all()

# 3. Agendamentos
@app.get("/quadras/{quadra_id}/agendamentos/", response_model=List[schemas.AgendamentoResponse])
def listar_agendamentos_quadra(quadra_id: int, db: Session = Depends(get_db)):
    agendamentos = db.query(models.Agendamento).filter(models.Agendamento.quadra_id == quadra_id).all()
    return agendamentos

@app.post("/agendamentos/", response_model=schemas.AgendamentoResponse)
def criar_agendamento(agendamento: schemas.AgendamentoCreate, db: Session = Depends(get_db), usuario_atual: models.Usuario = Depends(get_usuario_atual)):
    # Valida se a quadra existe
    quadra = db.query(models.Quadra).filter(models.Quadra.id == agendamento.quadra_id).first()
    if not quadra:
        raise HTTPException(status_code=404, detail="Quadra não encontrada")
    
    # Lógica de negócio: Impede agendamento sobreposto (conflito de horário)
    conflito = db.query(models.Agendamento).filter(
        models.Agendamento.quadra_id == agendamento.quadra_id,
        or_(
            (models.Agendamento.data_hora_inicio <= agendamento.data_hora_inicio) & (models.Agendamento.data_hora_fim > agendamento.data_hora_inicio),
            (models.Agendamento.data_hora_inicio < agendamento.data_hora_fim) & (models.Agendamento.data_hora_fim >= agendamento.data_hora_fim),
            (models.Agendamento.data_hora_inicio >= agendamento.data_hora_inicio) & (models.Agendamento.data_hora_fim <= agendamento.data_hora_fim)
        )
    ).first()

    if conflito:
        raise HTTPException(status_code=400, detail="Horário indisponível para esta quadra.")

    # Salva o agendamento amarrado ao ID do usuário do token
    novo_agendamento = models.Agendamento(
        usuario_id=usuario_atual.id, 
        quadra_id=agendamento.quadra_id,
        data_hora_inicio=agendamento.data_hora_inicio,
        data_hora_fim=agendamento.data_hora_fim
    )
    db.add(novo_agendamento)
    db.commit()
    db.refresh(novo_agendamento)
    return novo_agendamento

@app.delete("/quadras/{quadra_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_quadra(quadra_id: int, db: Session = Depends(get_db)):
    # Procura a quadra pelo ID
    quadra_query = db.query(models.Quadra).filter(models.Quadra.id == quadra_id)
    quadra = quadra_query.first()
    
    if not quadra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quadra não encontrada")
        
    # Elimina do banco e salva a alteração
    quadra_query.delete(synchronize_session=False)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)