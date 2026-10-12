import os
import tempfile
import unittest
import hashlib
from unittest.mock import patch
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
import recuperacao
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

    def mail_config(self):
        return patch.dict(os.environ, {
            'BREVO_API_KEY': 'test-key-not-real', 'EMAIL_FROM': 'sender@example.com',
            'PUBLIC_BASE_URL': 'https://quadra.example.com',
        })

    def test_recovery_single_use_hash_and_session_revocation(self):
        old_session = self.account('admin@example.com')
        with self.mail_config(), patch('recuperacao.enviar_email') as mail:
            known = self.client.post('/auth/recuperar-senha', json={'email': 'ADMIN@example.com'}, headers={'Host': 'attacker.example'})
            unknown = self.client.post('/auth/recuperar-senha', json={'email': 'missing@example.com'})
            self.assertEqual(known.status_code, 200)
            self.assertEqual(known.json(), unknown.json())
            self.assertEqual(mail.call_count, 1)
            recipient, link = mail.call_args.args
            self.assertEqual(recipient, 'admin@example.com')
            self.assertTrue(link.startswith('https://quadra.example.com/redefinir-senha.html#token='))
            token = link.split('#token=')[1]
            self.assertNotIn(token, known.text)
            with main.SessionLocal() as db:
                row = db.query(models.RecuperacaoSenha).one()
                self.assertEqual(row.token_hash, hashlib.sha256(token.encode()).hexdigest())
                self.assertNotIn(token, row.token_hash)
            body = {'token': token, 'senha': 'NovaSenha123!'}
            self.assertEqual(self.client.post('/auth/redefinir-senha', json=body).status_code, 200)
            self.assertEqual(self.client.post('/auth/redefinir-senha', json=body).status_code, 400)
            self.assertEqual(self.client.post('/token', data={'username': recipient, 'password': 'Teste12345'}).status_code, 401)
            new = self.client.post('/token', data={'username': recipient, 'password': body['senha']})
            self.assertEqual(new.status_code, 200)
            court = {'nome': 'Teste', 'tipo': 'Futsal', 'localizacao': 'Centro'}
            self.assertEqual(self.client.post('/quadras/', headers=old_session, json=court).status_code, 401)
            self.assertEqual(self.client.post('/quadras/', headers={'Authorization': 'Bearer ' + new.json()['access_token']}, json=court).status_code, 200)

    def test_recovery_expiry_replacement_and_password_validation(self):
        self.account('user@example.com')
        with self.mail_config(), patch('recuperacao.enviar_email') as mail:
            self.client.post('/auth/recuperar-senha', json={'email': 'user@example.com'})
            old_token = mail.call_args.args[1].split('#token=')[1]
            self.client.post('/auth/recuperar-senha', json={'email': 'user@example.com'})
            token = mail.call_args.args[1].split('#token=')[1]
            self.assertEqual(self.client.post('/auth/redefinir-senha', json={'token': old_token, 'senha': 'NovaSenha123'}).status_code, 400)
            for password in ['curta', 'é' * 37]:
                self.assertEqual(self.client.post('/auth/redefinir-senha', json={'token': token, 'senha': password}).status_code, 422)
            with main.SessionLocal() as db:
                db.query(models.RecuperacaoSenha).one().expira_em = recuperacao.agora() - timedelta(seconds=1)
                db.commit()
            self.assertEqual(self.client.post('/auth/redefinir-senha', json={'token': token, 'senha': 'NovaSenha123'}).status_code, 400)
            self.assertEqual(self.client.post('/token', data={'username': 'user@example.com', 'password': 'Teste12345'}).status_code, 200)

    def test_recovery_rate_limit_and_missing_config(self):
        with patch.dict(os.environ, {'BREVO_API_KEY': '', 'EMAIL_FROM': '', 'PUBLIC_BASE_URL': ''}), patch('recuperacao.enviar_email') as mail:
            self.assertFalse(self.client.get('/auth/recuperacao-disponivel').json()['disponivel'])
            self.assertEqual(self.client.post('/auth/recuperar-senha', json={'email': 'missing@example.com'}).status_code, 503)
            mail.assert_not_called()
        with self.mail_config():
            self.assertTrue(self.client.get('/auth/recuperacao-disponivel').json()['disponivel'])
            for _ in range(3):
                self.assertEqual(self.client.post('/auth/recuperar-senha', json={'email': 'missing@example.com'}).status_code, 200)
            self.assertEqual(self.client.post('/auth/recuperar-senha', json={'email': 'missing@example.com'}).status_code, 429)
            for i in range(6):
                self.assertEqual(self.client.post('/auth/recuperar-senha', json={'email': f'x{i}@example.com'}).status_code, 200)
            self.assertEqual(self.client.post('/auth/recuperar-senha', json={'email': 'another@example.com'}).status_code, 429)

    def test_recovery_frontend_and_no_token_access(self):
        response = self.client.get('/redefinir-senha.html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['referrer-policy'], 'no-referrer')
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertIn('Perdeu sua senha?', self.client.get('/index.html').text)
        self.assertEqual(self.client.post('/auth/redefinir-senha', json={'token': 'x' * 43, 'senha': 'NovaSenha123'}).status_code, 400)

    def test_email_provider_request_and_failure_logging(self):
        import json
        with self.mail_config(), patch('recuperacao.urlopen') as network:
            network.return_value.__enter__.return_value.status = 201
            recuperacao.enviar_email('user@example.com', 'https://quadra.example.com/redefinir-senha.html#token=test')
            request = network.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.brevo.com/v3/smtp/email')
            data = json.loads(request.data)
            self.assertEqual(data['to'], [{'email': 'user@example.com'}])
            self.assertEqual(data['sender']['email'], 'sender@example.com')
            self.assertIn('#token=test', data['textContent'])
        self.account('user@example.com')
        with self.mail_config(), patch('recuperacao.enviar_email', side_effect=RuntimeError('private provider response')), self.assertLogs('recuperacao', level='ERROR') as logs:
            response = self.client.post('/auth/recuperar-senha', json={'email': 'user@example.com'})
            self.assertEqual(response.status_code, 200)
            output = ' '.join(logs.output)
            self.assertNotIn('user@example.com', output)
            self.assertNotIn('private provider response', output)


if __name__ == '__main__':
    unittest.main()
