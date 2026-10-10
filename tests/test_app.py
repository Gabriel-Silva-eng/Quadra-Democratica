import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

TEMP = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(TEMP.name) / 'test.sqlite3').as_posix()
os.environ['SECRET_KEY'] = 'test-only-secret-key-with-at-least-32-characters'
os.environ['ADMIN_EMAILS'] = 'admin@example.com'
os.environ['APP_ENV'] = 'test'

from fastapi.testclient import TestClient
import main
import models
from database import engine


def tearDownModule():
    engine.dispose()
    TEMP.cleanup()


class AppTests(unittest.TestCase):
    def setUp(self):
        models.Base.metadata.drop_all(engine)
        models.Base.metadata.create_all(engine)
        self.client = TestClient(main.app)

    def account(self, email):
        response = self.client.post('/usuarios/', json={'nome': 'Teste', 'email': email, 'senha': 'Teste12345'})
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.post('/token', data={'username': email, 'password': 'Teste12345'})
        self.assertEqual(response.status_code, 200, response.text)
        return {'Authorization': 'Bearer ' + response.json()['access_token']}

    def test_frontend_and_health(self):
        self.assertIn('text/html', self.client.get('/').headers['content-type'])
        self.assertEqual(self.client.get('/health').json()['status'], 'ok')
        for path in ['/index.html', '/dashboard.html', '/assets/style.css', '/assets/app.js', '/assets/dashboard.js']:
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_catalog_import_is_once_and_preserves_edits(self):
        from catalogo import importar_catalogo
        from sqlalchemy.orm import Session
        importar_catalogo(engine)
        response = self.client.get('/quadras/').json()
        self.assertEqual(len(response), 9)
        self.assertEqual(sum(bool(q['imagem_url']) for q in response), 9)
        for court in response:
            if court['imagem_url']:
                self.assertEqual(self.client.get(court['imagem_url']).status_code, 200)
        with Session(engine) as db:
            court = db.get(models.Quadra, response[0]['id'])
            court.localizacao = 'Endereço atualizado'
            db.commit()
        importar_catalogo(engine)
        updated = self.client.get('/quadras/').json()
        self.assertEqual(len(updated), 9)
        self.assertEqual(updated[0]['localizacao'], 'Endereço atualizado')

    def test_photo_migration_preserves_existing_court(self):
        from catalogo import importar_catalogo, VERSAO
        from sqlalchemy.orm import Session
        with Session(engine) as db:
            db.add(models.ImportacaoCatalogo(chave=VERSAO))
            db.add(models.Quadra(id=42, nome='Centro Esportivo Miguel Vieira', localizacao='Endereço existente', tipo='Tipo existente'))
            db.commit()
        importar_catalogo(engine)
        response = self.client.get('/quadras/').json()
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], 42)
        self.assertEqual(response[0]['localizacao'], 'Endereço existente')
        self.assertEqual(response[0]['imagem_url'], '/assets/quadras/miguel-vieira.jpg')

    def test_admin_permissions_and_reservations(self):
        user = self.account('user@example.com')
        admin = self.account('admin@example.com')
        court = {'nome': 'Quadra Teste', 'tipo': 'Futsal', 'localizacao': 'Centro'}
        self.assertEqual(self.client.post('/quadras/', json=court).status_code, 401)
        self.assertEqual(self.client.post('/quadras/', headers=user, json=court).status_code, 403)
        response = self.client.post('/quadras/', headers=admin, json=court)
        self.assertEqual(response.status_code, 200, response.text)
        court_id = response.json()['id']
        self.assertEqual(self.client.delete(f'/quadras/{court_id}').status_code, 401)
        self.assertEqual(self.client.delete(f'/quadras/{court_id}', headers=user).status_code, 403)
        start = datetime.now().replace(microsecond=0) + timedelta(days=1)
        booking = {'quadra_id': court_id, 'data_hora_inicio': start.isoformat(), 'data_hora_fim': (start + timedelta(hours=1)).isoformat()}
        self.assertEqual(self.client.post('/agendamentos/', headers=user, json=booking).status_code, 200)
        self.assertEqual(self.client.post('/agendamentos/', headers=user, json=booking).status_code, 400)
        self.assertEqual(self.client.delete(f'/quadras/{court_id}', headers=admin).status_code, 409)
        booking['data_hora_inicio'] = booking['data_hora_fim']
        booking['data_hora_fim'] = (start + timedelta(hours=2)).isoformat()
        self.assertEqual(self.client.post('/agendamentos/', headers=user, json=booking).status_code, 200)
        booking['data_hora_fim'] = booking['data_hora_inicio']
        self.assertEqual(self.client.post('/agendamentos/', headers=user, json=booking).status_code, 422)

    def test_password_validation_and_invalid_token(self):
        self.assertEqual(self.client.post('/usuarios/', json={'nome': 'Teste', 'email': 'a@example.com', 'senha': 'x' * 73}).status_code, 422)
        self.assertEqual(self.client.get('/quadras/').status_code, 200)
        self.assertEqual(self.client.post('/quadras/', headers={'Authorization': 'Bearer invalid'}, json={'nome': 'X', 'tipo': 'Y', 'localizacao': 'Z'}).status_code, 401)


if __name__ == '__main__':
    unittest.main()
