import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# O banco será um arquivo local chamado quadralivre.sqlite3
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quadralivre.sqlite3")
if SQLALCHEMY_DATABASE_URL.startswith(("postgres://", "postgresql://")):
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://" + SQLALCHEMY_DATABASE_URL.split("://", 1)[1]
if os.getenv("APP_ENV") == "production" and SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    raise RuntimeError("Configure DATABASE_URL com PostgreSQL em produção.")

# connect_args={"check_same_thread": False} é uma exigência do SQLite ao trabalhar com FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base para criar os modelos
Base = declarative_base()
