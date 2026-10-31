# Publicação no Render

Interface e API são servidas pela mesma aplicação FastAPI.

O projeto publicado oferece previsão diária para Potim ao selecionar a data
da reserva. O navegador consulta a API Forecast pública do Open-Meteo e mostra
condição, temperaturas mínima/máxima e probabilidade máxima de chuva. O limite
da previsão é 16 dias; para datas mais distantes, não há previsão disponível.
Nenhuma chave adicional é necessária. A previsão pode mudar e serve apenas
como referência.

Cada quadra tem uma área de comentários. A leitura é pública e publicar exige
login. Comentários têm de 3 a 1.000 caracteres; as listagens retornam os 100
mais recentes. O autor ou a administração pode excluir um comentário pela API.

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
O catálogo municipal de `quadras.json` é importado uma única vez no banco,
incluindo as nove fotos em `frontend/quadras`. Reinícios não recriam quadras
excluídas nem sobrescrevem alterações posteriores. Modalidades não informadas
ficam como "A confirmar"; endereços específicos ainda devem ser cadastrados.
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

O navegador consulta a previsão do Open-Meteo diretamente; a conexão com a
internet é necessária para exibi-la. Se o serviço externo estiver indisponível,
o site mantém a reserva disponível e mostra uma mensagem informativa.

## Testes

```powershell
pip install --no-cache-dir -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Recuperação de senha por e-mail

O login inclui **Perdeu sua senha?**. O envio fica indisponível até configurar:

- `PUBLIC_BASE_URL`: `https://quadra-democratica.onrender.com` (origem fixa HTTPS).
- `BREVO_API_KEY`: chave de API do Brevo, guardada apenas em Environment no Render.
- `EMAIL_FROM`: e-mail do remetente verificado na conta Brevo.

Crie sua conta em https://www.brevo.com, confirme seu e-mail, adicione e verifique
um remetente em Senders, Domains & Dedicated IPs e gere uma chave em SMTP & API
→ API Keys (não uma chave SMTP). Faça essa configuração diretamente no provedor;
não envie chaves no chat, não as grave no código nem no Git. O plano gratuito do
Render bloqueia SMTP, por isso usamos a API HTTPS do Brevo. Sem domínio próprio,
o Brevo pode substituir o domínio do remetente por brevosend.com; confira as
regras atuais do provedor e teste a entrega, inclusive spam.

Depois de salvar essas três variáveis no Render e publicar/reiniciar, solicite
um link pela tela de login e confirme que ele chegou. Solicitações conhecidas e
desconhecidas recebem a mesma resposta; isso não comprova entrega. Se necessário,
verifique o painel de e-mails transacionais do Brevo. Falhas são registradas sem
endereços, links ou segredos. O link expira em 15 minutos, é usado uma única vez,
e cada nova solicitação invalida os links anteriores. A redefinição invalida as
sessões antigas. Senhas e tokens em texto nunca são gravados no banco.
