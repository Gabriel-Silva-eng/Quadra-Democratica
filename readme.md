# 🏀 Quadra Democrática

Reserva e gestão de quadras esportivas comunitárias — Projeto Integrador.

Conectar moradores a quadras públicas e comunitárias, evitando conflito de horário e organizando o uso compartilhado do espaço com foco em performance, acessibilidade e segurança (Security by Design).

---

## Índice

- [Sobre](#sobre)
- [Stack Tecnológica](#stack-tecnológica)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Rodar Localmente](#como-rodar-localmente)
- [API e Rotas](#api-e-rotas)
- [Requisitos do PI](#requisitos-do-pi)
- [Licença](#licença)

---

## Sobre

Quadra Democrática é um sistema web pensado para facilitar a reserva e gestão de quadras. O diferencial deste protótipo é a aplicação de boas práticas de segurança desde a base, utilizando hashing irreversível de senhas e autenticação via tokens JWT (JSON Web Tokens).

Este repositório contém um back-end construído em Python (FastAPI) e um front-end leve feito puramente em HTML, CSS e JavaScript (Vanilla), sem dependência de frameworks pesados, garantindo alta performance e controle total sobre a acessibilidade.

---

## Stack Tecnológica

- **Front-end:** HTML5, CSS3 (Alto Contraste), JavaScript Vanilla (Fetch API)
- **Back-end:** Python 3 + FastAPI (API RESTful)
- **Segurança:** PyJWT (Tokens), Passlib/Bcrypt (Hashing de senhas), CORS Middleware
- **Banco de Dados:** SQLite (via `SQLAlchemy` ORM)
- **Servidor:** Uvicorn (ASGI)
- **Controle de Versão:** Git / GitHub

---

## Estrutura do Projeto

```text
QuadraLivre/
├── main.py                # Ponto de entrada da API e rotas principais
├── database.py            # Configuração do banco SQLite e SQLAlchemy
├── models.py              # Modelos de tabelas do banco de dados (ORM)
├── schemas.py             # Validação de dados de entrada/saída (Pydantic)
├── requirements.txt       # Dependências do Python
├── frontend/
│   ├── index.html         # Tela de Login e Cadastro
│   ├── dashboard.html     # Painel de agendamento e listagem de quadras
│   ├── style.css          # Estilos com variáveis de tema e foco em acessibilidade
│   ├── app.js             # Lógica de autenticação e comunicação com API
│   └── dashboard.js       # Regras de negócio do front-end e validação de tempo
```

---

## Como Rodar Localmente

Siga estes passos em terminais separados para levantar os serviços.

**1) Back-end (Porta 8000)**

Na raiz do projeto, crie e ative o ambiente virtual, instale as dependências e rode o Uvicorn:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*A documentação interativa da API (Swagger) ficará disponível em `http://127.0.0.1:8000/docs`.*

**2) Front-end (Porta 5500)**

Em um novo terminal, navegue até a pasta do front-end e suba um servidor local:

```bash
cd frontend
python3 -m http.server 5500
```
Abra `http://localhost:5500` no seu navegador.

---

## API e Rotas

A API foi documentada automaticamente pelo FastAPI. Abaixo os principais endpoints:

| Método | Rota | Descrição | Requer Token? |
|---|---|---|---|
| GET | `/` | Status do servidor | Não |
| POST | `/usuarios/` | Cria um novo usuário (senha passa por hash bcrypt) | Não |
| POST | `/token` | Autenticação (OAuth2). Retorna o JWT de acesso | Não |
| GET | `/quadras/` | Lista todas as quadras disponíveis | Não |
| POST | `/quadras/` | Cadastra nova quadra no sistema | Sim |
| GET | `/quadras/{id}/agendamentos/`| Retorna os horários já reservados de uma quadra específica | Não |
| POST | `/agendamentos/` | Cria reserva (Valida conflito de horário → Erro `400`) | Sim |

---

## Requisitos do PI — Como este projeto atende

| Requisito | Como é atendido |
|---|---|
| **Framework web** | FastAPI (Back-end) — alta performance e validação estrita. |
| **Banco de dados** | SQLite relacional gerenciado via ORM SQLAlchemy. |
| **Script web** | JavaScript Vanilla controlando DOM, consumindo API assincronamente (Fetch) e validando regras de tempo no cliente. |
| **Uso de API** | Front-end totalmente desacoplado, consumindo a própria API REST. |
| **Acessibilidade** | Labels explicitamente associados, contraste AA (tema escuro/azul), tags `aria-live`, navegação 100% via teclado. |
| **Controle de versão** | Repositório Git com commits atômicos. |
| **Segurança (Extra)**| Proteção contra SQL Injection (ORM), senhas criptografadas e rotas blindadas com JWT. |
| **Nuvem** | *Próximo passo:* Deploy do back-end (Render) e front-end (GitHub Pages/Vercel). |
| **Testes** | *Próximo passo:* Implementação de suíte de testes com `pytest`. |

---

## Licença

Este projeto se encontra sob a licença MIT.
