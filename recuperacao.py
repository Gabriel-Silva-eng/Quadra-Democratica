"""Recuperação por e-mail: segredo aleatório, persistido apenas como hash."""
import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from urllib.request import Request as EmailRequest, urlopen

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas
from database import SessionLocal

logger = logging.getLogger(__name__)
MENSAGEM = "Se houver uma conta com esse e-mail, você receberá um link de recuperação. Confira também a caixa de spam."


def agora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def assinatura_senha(secret, senha_hash):
    return hmac.new(secret.encode(), senha_hash.encode(), hashlib.sha256).hexdigest()


def configuracao_email():
    chave = os.getenv("BREVO_API_KEY", "")
    remetente = os.getenv("EMAIL_FROM", "")
    base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    url = urlsplit(base)
    valido = url.scheme == "https" or (
        os.getenv("APP_ENV") != "production" and url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1"}
    )
    if not chave or "@" not in remetente or not valido or not url.netloc or url.query or url.fragment or url.username:
        return None
    return chave, remetente, base


def enviar_email(email, link):
    chave, remetente, _ = configuracao_email()
    dados = {
        "sender": {"name": "Quadra Democrática", "email": remetente},
        "to": [{"email": email}],
        "subject": "Redefina sua senha — Quadra Democrática",
        "textContent": (
            "Recebemos uma solicitação para redefinir sua senha na Quadra Democrática.\n\n"
            f"Abra este link para escolher uma nova senha:\n{link}\n\n"
            "O link expira em 15 minutos e só pode ser usado uma vez. "
            "Se você não pediu a alteração, ignore este e-mail. Sua senha continua a mesma."
        ),
    }
    pedido = EmailRequest(
        "https://api.brevo.com/v3/smtp/email", data=json.dumps(dados).encode(),
        headers={"api-key": chave, "Content-Type": "application/json", "Accept": "application/json"}, method="POST",
    )
    with urlopen(pedido, timeout=10) as resposta:
        if resposta.status != 201:
            raise RuntimeError("Envio não aceito")


def limitar(db, secret, identidade, maximo):
    """Contador persistente e atômico; não guarda e-mail ou endereço IP."""
    chave = assinatura_senha(secret, identidade)
    atual = agora()
    corte = atual - timedelta(minutes=15)
    db.query(models.LimiteRecuperacao).filter(models.LimiteRecuperacao.inicio < atual - timedelta(days=1)).delete()
    db.execute(update(models.LimiteRecuperacao).where(
        models.LimiteRecuperacao.chave == chave, models.LimiteRecuperacao.inicio <= corte,
    ).values(inicio=atual, tentativas=0))
    db.commit()
    resultado = db.execute(update(models.LimiteRecuperacao).where(
        models.LimiteRecuperacao.chave == chave, models.LimiteRecuperacao.tentativas < maximo,
    ).values(tentativas=models.LimiteRecuperacao.tentativas + 1))
    if resultado.rowcount:
        db.commit()
        return
    if db.get(models.LimiteRecuperacao, chave):
        db.rollback()
        raise HTTPException(429, "Muitas tentativas. Aguarde 15 minutos e tente novamente.")
    db.add(models.LimiteRecuperacao(chave=chave, inicio=atual, tentativas=1))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        limitar(db, secret, identidade, maximo)


def preparar_email(email, secret):
    try:
        with SessionLocal() as db:
            usuario = db.query(models.Usuario).filter(models.Usuario.email == email).with_for_update().first()
            if not usuario:
                return
            atual = agora()
            db.query(models.RecuperacaoSenha).filter(models.RecuperacaoSenha.expira_em < atual).delete()
            # Uma solicitação nova substitui os links anteriores da mesma conta.
            db.query(models.RecuperacaoSenha).filter(models.RecuperacaoSenha.usuario_id == usuario.id).delete()
            token = secrets.token_urlsafe(32)
            db.add(models.RecuperacaoSenha(
                token_hash=hashlib.sha256(token.encode()).hexdigest(), usuario_id=usuario.id,
                assinatura_senha=assinatura_senha(secret, usuario.senha_hash), expira_em=atual + timedelta(minutes=15),
            ))
            db.commit()
        _, _, base = configuracao_email()
        # O fragmento não vai para os logs HTTP nem para o cabeçalho Referer.
        enviar_email(email, f"{base}/redefinir-senha.html#token={token}")
    except Exception:
        # Nunca registrar destinatário, senha, link, chave ou conteúdo da resposta do provedor.
        logger.error("Não foi possível enviar um e-mail de recuperação. Verifique o provedor de envio.")


def criar_router(secret, pwd_context, get_db):
    router = APIRouter(prefix="/auth")

    @router.get("/recuperacao-disponivel")
    def disponibilidade(response: Response):
        response.headers["Cache-Control"] = "no-store"
        return {"disponivel": bool(configuracao_email())}

    @router.post("/recuperar-senha")
    def recuperar(dados: schemas.RecuperarSenha, request: Request, tarefas: BackgroundTasks, response: Response, db: Session = Depends(get_db)):
        response.headers["Cache-Control"] = "no-store"
        if not configuracao_email():
            raise HTTPException(503, "A recuperação por e-mail ainda está sendo configurada. Tente novamente mais tarde.")
        limitar(db, secret, "solicitacao-ip:" + request.client.host, 10)
        limitar(db, secret, "solicitacao-email:" + dados.email, 3)
        tarefas.add_task(preparar_email, dados.email, secret)
        return {"mensagem": MENSAGEM}

    @router.post("/redefinir-senha")
    def redefinir(dados: schemas.RedefinirSenha, request: Request, response: Response, db: Session = Depends(get_db)):
        response.headers["Cache-Control"] = "no-store"
        limitar(db, secret, "redefinicao-ip:" + request.client.host, 20)
        digest = hashlib.sha256(dados.token.encode()).hexdigest()
        recuperacao = db.get(models.RecuperacaoSenha, digest)
        invalido = HTTPException(400, "Link inválido ou expirado. Solicite um novo link de recuperação.")
        if not recuperacao:
            raise invalido
        usuario = db.query(models.Usuario).filter(models.Usuario.id == recuperacao.usuario_id).with_for_update().first()
        recuperacao = db.query(models.RecuperacaoSenha).filter(models.RecuperacaoSenha.token_hash == digest).populate_existing().with_for_update().first()
        if not usuario or not recuperacao or recuperacao.usado_em or recuperacao.expira_em <= agora():
            raise invalido
        if not hmac.compare_digest(recuperacao.assinatura_senha, assinatura_senha(secret, usuario.senha_hash)):
            raise invalido
        resultado = db.execute(update(models.RecuperacaoSenha).where(
            models.RecuperacaoSenha.token_hash == digest, models.RecuperacaoSenha.usado_em.is_(None),
        ).values(usado_em=agora()))
        if resultado.rowcount != 1:
            db.rollback()
            raise invalido
        usuario.senha_hash = pwd_context.hash(dados.senha)
        db.commit()
        return {"mensagem": "Senha alterada. Entre com sua nova senha."}

    return router
