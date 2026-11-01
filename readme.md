> **Aplicação publicada:** [quadra-democratica.onrender.com](https://quadra-democratica.onrender.com/).
> Interface e API são servidas juntas pelo FastAPI. Para instalar, executar localmente,
> configurar o Render e o e-mail de recuperação, consulte [DEPLOY.md](DEPLOY.md).

<div align="center">
<pre>
  ```  
      ___           ___                                    ___           ___           ___   
     /__/\         /__/\        ___           ___         /  /\         /  /\         /  /\  
     \  \:\        \  \:\      /  /\         /__/\       /  /:/_       /  /:/_       /  /::\ 
      \  \:\        \  \:\    /  /:/         \  \:\     /  /:/ /\     /  /:/ /\     /  /:/\:\
  ___  \  \:\   _____\__\:\  /__/::\          \  \:\   /  /:/ /:/_   /  /:/ /::\   /  /:/~/:/
 /__/\  \__\:\ /__/::::::::\ \__\/\:\__   ___  \__\:\ /__/:/ /:/ /\ /__/:/ /:/\:\ /__/:/ /:/ 
 \  \:\ /  /:/ \  \:\~~\~~\/    \  \:\/\ /__/\ |  |:| \  \:\/:/ /:/ \  \:\/:/~/:/ \  \:\/:/  
  \  \:\  /:/   \  \:\  ~~~      \__\::/ \  \:\|  |:|  \  \::/ /:/   \  \::/ /:/   \  \::/   
   \  \:\/:/     \  \:\          /__/:/   \  \:\__|:|   \  \:\/:/     \__\/ /:/     \  \:\   
    \  \::/       \  \:\         \__\/     \__\::::/     \  \::/        /__/:/       \  \:\  
     \__\/         \__\/                       ~~~~       \__\/         \__\/         \__\/  
 </pre></div> 
                    

# 🏀 Quadra Democrática

Reserva e gestão de quadras esportivas comunitárias em Potim/SP — Projeto Integrador.

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

Quadra Democrática facilita a reserva e a gestão das quadras públicas de Potim. Usuários podem consultar os espaços, ver horários ocupados, solicitar reservas e ler ou publicar comentários. Ao escolher a data de utilização, o painel também consulta a previsão diária do tempo para Potim. A previsão usa a API pública Open-Meteo e está disponível para datas dentro do horizonte de até 16 dias; previsões podem mudar.

O sistema combina uma API Python/FastAPI, um front-end em HTML, CSS e JavaScript e banco PostgreSQL na hospedagem. O login usa senhas com hash bcrypt e tokens JWT. Visitantes podem ler comentários associados a cada quadra; apenas usuários autenticados podem publicar. O autor e a administração podem excluir comentários pela API. A recuperação de senha é enviada pelo Brevo quando o serviço está configurado.

---

## Stack Tecnológica

- **Front-end:** HTML5, CSS3 (Alto Contraste), JavaScript Vanilla (Fetch API)
- **Back-end:** Python 3 + FastAPI (API RESTful)
- **Segurança:** PyJWT (Tokens), Passlib/Bcrypt (Hashing de senhas), CORS Middleware
- **Banco de Dados:** PostgreSQL na produção e SQLite no desenvolvimento local (via `SQLAlchemy` ORM)
- **Servidor:** Uvicorn (ASGI)
- **Controle de Versão:** Git / GitHub

---

## Estrutura do Projeto

```text
Quadra-Democratica/
├── main.py                # Ponto de entrada da API e rotas principais
├── database.py            # Configuração do banco SQLite e SQLAlchemy
├── models.py              # Modelos de tabelas do banco de dados (ORM)
├── schemas.py             # Validação de dados de entrada/saída (Pydantic)
├── requirements.txt       # Dependências do Python
├── catalogo.py           # Importação inicial do catálogo de quadras
├── quadras.json          # Catálogo inicial de Potim
├── DEPLOY.md             # Execução local e instruções de hospedagem
├── frontend/
│   ├── index.html         # Tela de Login e Cadastro
│   ├── dashboard.html     # Painel de agendamento e listagem de quadras
│   ├── style.css          # Estilos com variáveis de tema e foco em acessibilidade
│   ├── app.js             # Lógica de autenticação e comunicação com API
│   └── dashboard.js       # Regras de negócio do front-end e validação de tempo
```

---

## Como Rodar Localmente

Na raiz do projeto, crie e ative o ambiente virtual, instale as dependências e rode a aplicação:

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```
Abra `http://127.0.0.1:8000`. O painel da API fica em `/docs` e o estado do serviço em `/health`. A aplicação FastAPI também serve os arquivos do front-end; não é necessário iniciar outro servidor estático.

---

## API e Rotas

A API foi documentada automaticamente pelo FastAPI. Abaixo os principais endpoints:

| Método | Rota | Descrição | Requer Token? |
|---|---|---|---|
| GET | `/` | Status do servidor | Não |
| POST | `/usuarios/` | Cria um novo usuário (senha passa por hash bcrypt) | Não |
| POST | `/token` | Autenticação (OAuth2). Retorna o JWT de acesso | Não |
| GET | `/quadras/` | Lista todas as quadras disponíveis | Não |
| POST | `/quadras/` | Cadastra nova quadra no sistema (somente administração) | Sim |
| GET | `/quadras/{id}/agendamentos/`| Retorna os horários já reservados de uma quadra específica | Não |
| POST | `/agendamentos/` | Cria reserva (Valida conflito de horário → Erro `400`) | Sim |
| GET | `/quadras/{id}/comentarios/` | Lista até os 100 comentários mais recentes da quadra | Não |
| POST | `/quadras/{id}/comentarios/` | Publica comentário de 3 a 1.000 caracteres | Sim |
| DELETE | `/comentarios/{id}` | Exclui comentário próprio ou pela administração | Sim |

### Previsão do tempo

Ao selecionar uma data no formulário de reserva, o navegador consulta a previsão diária de Potim (mínima e máxima, condição do tempo e probabilidade máxima de chuva). A consulta usa a [API Forecast do Open-Meteo](https://open-meteo.com/en/docs), sem chave de API. O serviço oferece previsões de até 16 dias; para datas mais distantes, o painel informa que ainda não há previsão disponível. A previsão é estimativa e deve ser consultada novamente perto do uso.

### Comentários das quadras

Os comentários são vinculados à quadra e guardados no banco de dados. Qualquer visitante pode ler; é necessário entrar na conta para publicar. O autor do comentário e a administração podem removê-lo pela API. A interface exibe os comentários e o formulário de publicação no cartão de cada quadra.

---

## Requisitos do PI — Como este projeto atende

| Requisito | Como é atendido |
|---|---|
| **Framework web** | FastAPI (Back-end) — alta performance e validação estrita. |
| **Banco de dados** | PostgreSQL em produção e SQLite para uso local, gerenciados via ORM SQLAlchemy. |
| **Script web** | JavaScript Vanilla controlando DOM, consumindo API assincronamente (Fetch) e validando regras de tempo no cliente. |
| **Uso de API** | Front-end consome a API REST do sistema e a API Forecast do Open-Meteo para a previsão. |
| **Acessibilidade** | Labels explicitamente associados, contraste AA (tema escuro/azul), tags `aria-live`, navegação 100% via teclado. |
| **Controle de versão** | Repositório Git com commits atômicos. |
| **Segurança (Extra)**| Proteção contra SQL Injection (ORM), senhas criptografadas e rotas blindadas com JWT. |
| **Nuvem** | Aplicação publicada no Render com PostgreSQL. Consulte [DEPLOY.md](DEPLOY.md) para configuração. |
| **Testes** | Testes automatizados disponíveis em `tests/`; execute as instruções de [DEPLOY.md](DEPLOY.md). |

---

## Licença

Este projeto se encontra sob a licença MIT.
