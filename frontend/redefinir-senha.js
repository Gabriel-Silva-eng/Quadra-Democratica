const form = document.getElementById('form-redefinir');
const status = document.getElementById('mensagem-status');
const botao = document.getElementById('btn-salvar-senha');
let tokenRecuperacao = new URLSearchParams(window.location.hash.slice(1)).get('token');
history.replaceState(null, '', window.location.pathname);
function mensagem(texto, erro) {
    status.textContent = texto;
    status.className = erro ? 'msg-erro' : 'msg-sucesso';
}
if (!tokenRecuperacao || !/^[A-Za-z0-9_-]{43,128}$/.test(tokenRecuperacao)) {
    form.hidden = true;
    mensagem('Abra o link recebido por e-mail. Se ele expirou, volte ao login e solicite outro em “Perdeu sua senha?”.', true);
}
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const senha = document.getElementById('nova-senha').value;
    const confirmacao = document.getElementById('confirmar-senha').value;
    if (senha !== confirmacao) {
        mensagem('As senhas não coincidem. Confira os dois campos.', true);
        return;
    }
    if (new TextEncoder().encode(senha).length > 72) {
        mensagem('A senha é muito longa. Use até 72 bytes de texto.', true);
        return;
    }
    botao.disabled = true;
    botao.textContent = 'Salvando...';
    try {
        const resposta = await fetch('/auth/redefinir-senha', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({token: tokenRecuperacao, senha})
        });
        const dados = await resposta.json();
        if (resposta.ok) {
            form.reset();
            form.hidden = true;
            tokenRecuperacao = null;
            localStorage.removeItem('quadralivre_token');
            mensagem(dados.mensagem, false);
        } else {
            mensagem(typeof dados.detail === 'string' ? dados.detail : 'Confira a senha informada. Use pelo menos 8 caracteres.', true);
        }
    } catch {
        mensagem('Falha de conexão. Tente novamente.', true);
    } finally {
        botao.disabled = false;
        botao.textContent = 'Salvar nova senha';
    }
});
