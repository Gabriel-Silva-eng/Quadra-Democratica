// Constante apontando para o seu backend local
const API_URL = 'http://127.0.0.1:8000';

// Elementos da Interface
const sessaoLogin = document.getElementById('sessao-login');
const sessaoCadastro = document.getElementById('sessao-cadastro');
const formLogin = document.getElementById('form-login');
const formCadastro = document.getElementById('form-cadastro');
const btnMostrarCadastro = document.getElementById('btn-mostrar-cadastro');
const btnMostrarLogin = document.getElementById('btn-mostrar-login');
const divStatus = document.getElementById('mensagem-status');

// --- NAVEGAÇÃO DE TELAS ---
btnMostrarCadastro.addEventListener('click', () => {
    sessaoLogin.classList.add('escondido');
    sessaoCadastro.classList.remove('escondido');
    limparStatus();
});

btnMostrarLogin.addEventListener('click', () => {
    sessaoCadastro.classList.add('escondido');
    sessaoLogin.classList.remove('escondido');
    limparStatus();
});

// --- FUNÇÃO PARA EXIBIR MENSAGENS (COM ACESSIBILIDADE) ---
function mostrarStatus(mensagem, tipo) {
    divStatus.textContent = mensagem;
    divStatus.className = ''; // Limpa classes antigas
    divStatus.classList.add(tipo === 'erro' ? 'msg-erro' : 'msg-sucesso');
}

function limparStatus() {
    divStatus.textContent = '';
    divStatus.className = 'escondido';
}

// --- CADASTRO DE USUÁRIO ---
formCadastro.addEventListener('submit', async (e) => {
    e.preventDefault(); // Impede a página de recarregar
    limparStatus();

    const nome = document.getElementById('cadastro-nome').value;
    const email = document.getElementById('cadastro-email').value;
    const senha = document.getElementById('cadastro-senha').value;

    try {
        const resposta = await fetch(`${API_URL}/usuarios/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ nome, email, senha })
        });

        if (resposta.ok) {
            mostrarStatus('Cadastro realizado com sucesso! Faça seu login.', 'sucesso');
            formCadastro.reset();
            // Volta para a tela de login após 2 segundos
            setTimeout(() => btnMostrarLogin.click(), 2000); 
        } else {
            const erroData = await resposta.json();
            mostrarStatus(erroData.detail || 'Erro ao cadastrar.', 'erro');
        }
    } catch (error) {
        mostrarStatus('Falha na comunicação com o servidor.', 'erro');
    }
});

// --- LOGIN DE USUÁRIO ---
formLogin.addEventListener('submit', async (e) => {
    e.preventDefault();
    limparStatus();

    const email = document.getElementById('login-email').value;
    const senha = document.getElementById('login-senha').value;

    // O FastAPI usa OAuth2 com formulário 'urlencoded', não JSON!
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', senha);

    try {
        const resposta = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (resposta.ok) {
            const dados = await resposta.json();
            // Salva o token no navegador
            localStorage.setItem('quadralivre_token', dados.access_token);
            mostrarStatus('Login efetuado! Redirecionando...', 'sucesso');
            
             // Redireciona para a página principal
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
            
        } else {
            mostrarStatus('E-mail ou senha incorretos.', 'erro');
        }
    } catch (error) {
        mostrarStatus('Falha na comunicação com o servidor.', 'erro');
    }
});