# Publicação no Render

Interface e API são servidas pela mesma aplicação FastAPI.

1. O Blueprint cria um PostgreSQL gratuito. Esse banco expira em 30 dias;
   exporte os dados ou migre antes disso. Não há backups no plano gratuito.
2. Abra https://dashboard.render.com/select-repo?type=blueprint e selecione
   `RaoniKir/Quadra-Democratica`. O arquivo `render.yaml` configura o serviço.
3. Informe `ADMIN_EMAILS` (seu e-mail de administração). `DATABASE_URL` será
   conectada ao banco e `SECRET_KEY` será gerada automaticamente pelo Render.
4. Após o deploy, abra a URL do serviço e crie sua conta com o e-mail escolhido.
5. Para cadastrar quadras, abra `/docs`, autentique em **Authorize** com e-mail
   e senha e use `POST /quadras/`. Apenas os e-mails em `ADMIN_EMAILS` podem
   cadastrar ou excluir quadras.

O banco local não é enviado ao GitHub nem migrado automaticamente.
O serviço gratuito pode suspender quando ocioso; o primeiro acesso pode demorar.
Não use SQLite no serviço de produção: a aplicação exige PostgreSQL.

## Execução local

Instale `requirements.txt` em um ambiente virtual e execute:

```powershell
$env:ADMIN_EMAILS = 'seu-email@exemplo.com'
python -m uvicorn main:app --reload
```

Abra http://127.0.0.1:8000. Os arquivos `.env` não são carregados automaticamente;
defina as variáveis no terminal ou na hospedagem.

## Testes

```powershell
pip install --no-cache-dir -r requirements-dev.txt
python -m unittest discover -s tests -v
```
