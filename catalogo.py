"""Importação única do catálogo municipal, preservando IDs e reservas."""
import json
from pathlib import Path
from sqlalchemy.orm import Session
from models import ImportacaoCatalogo, Quadra

VERSAO = "potim-nove-quadras-fotos-v1"


def importar_catalogo(engine):
    with Session(engine) as db:
        if db.get(ImportacaoCatalogo, VERSAO):
            return
        quadras = json.loads(Path(__file__).with_name("quadras.json").read_text(encoding="utf-8"))
        for dados in quadras:
            existente = db.query(Quadra).filter(Quadra.nome == dados["nome"]).first()
            if existente is None:
                db.add(Quadra(**dados))
            elif dados["imagem_url"]:
                existente.imagem_url = dados["imagem_url"]
        db.add(ImportacaoCatalogo(chave=VERSAO))
        db.commit()
