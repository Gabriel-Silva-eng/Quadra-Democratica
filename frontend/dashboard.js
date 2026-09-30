const API_URL = 'http://127.0.0.1:8000';
const token = localStorage.getItem('quadralivre_token');

if (!token) {
    window.location.href = 'index.html';
}

const btnSair = document.getElementById('btn-sair');
const selectQuadra = document.getElementById('select-quadra');
const inputData = document.getElementById('data-agendamento');
const listaQuadrasDiv = document.getElementById('lista-quadras');
const formAgendamento = document.getElementById('form-agendamento');
const divStatus = document.getElementById('mensagem-status');
const containerOcupados = document.getElementById('container-horarios-ocupados');
const listaOcupados = document.getElementById('lista-horarios-ocupados');

let agendamentosDaQuadraSelecionada = [];

function mostrarStatus(mensagem, tipo) {
    divStatus.textContent = mensagem;
    divStatus.className = ''; 
    divStatus.classList.add(tipo === 'erro' ? 'msg-erro' : 'msg-sucesso');
}

function limparStatus() {
    divStatus.textContent = '';
    divStatus.className = 'escondido';
}

btnSair.addEventListener('click', function() {
    localStorage.removeItem('quadralivre_token');
    window.location.href = 'index.html';
});

async function carregarQuadras() {
    try {
        const resposta = await fetch(API_URL + '/quadras/');
        if (resposta.ok) {
            const quadras = await resposta.json();
            renderizarQuadras(quadras);
            popularSelect(quadras);
        } else {
            listaQuadrasDiv.innerHTML = '<p style="color: var(--error-color)">Erro ao buscar quadras.</p>';
        }
    } catch (error) {
        listaQuadrasDiv.innerHTML = '<p style="color: var(--error-color)">Falha de conexão com o servidor.</p>';
    }
}

function renderizarQuadras(quadras) {
    if (quadras.length === 0) {
        listaQuadrasDiv.innerHTML = '<p>Nenhuma quadra cadastrada no sistema ainda.</p>';
        return;
    }
    
    listaQuadrasDiv.innerHTML = '<div class="grid-quadras"></div>';
    const gridDiv = listaQuadrasDiv.querySelector('.grid-quadras');

    quadras.forEach(function(q) {
        const card = document.createElement('div');
        card.className = 'card-quadra';
        
        const imgUrl = q.imagem_url ? q.imagem_url : 'https://via.placeholder.com/400x200.png?text=Imagem+Indisponivel';

        card.innerHTML = 
            '<img src="' + imgUrl + '" alt="Foto do espaço: ' + q.nome + '">' +
            '<div class="info-quadra">' +
                '<h3>' + q.nome + '</h3>' +
                '<p><strong>Modalidade:</strong> ' + q.tipo + '</p>' +
                '<p><strong>Local:</strong> ' + q.localizacao + '</p>' +
            '</div>';
            
        gridDiv.appendChild(card);
    });
}

function popularSelect(quadras) {
    selectQuadra.innerHTML = '<option value="">-- Selecione uma Quadra --</option>';
    quadras.forEach(function(q) {
        const option = document.createElement('option');
        option.value = q.id;
        option.textContent = q.nome + ' (' + q.tipo + ')';
        selectQuadra.appendChild(option);
    });
}

selectQuadra.addEventListener('change', async function(e) {
    const quadraId = e.target.value;
    if (!quadraId) {
        agendamentosDaQuadraSelecionada = [];
        atualizarListaOcupados();
        return;
    }

    try {
        const resposta = await fetch(API_URL + '/quadras/' + quadraId + '/agendamentos/');
        if (resposta.ok) {
            agendamentosDaQuadraSelecionada = await resposta.json();
            atualizarListaOcupados();
        }
    } catch (error) {
        console.error('Erro ao buscar agendamentos', error);
    }
});

inputData.addEventListener('change', atualizarListaOcupados);

function atualizarListaOcupados() {
    const dataSelecionada = inputData.value;
    const quadraId = selectQuadra.value;

    if (!dataSelecionada || !quadraId) {
        containerOcupados.classList.add('escondido');
        return;
    }

    const ocupadosNoDia = agendamentosDaQuadraSelecionada.filter(function(ag) {
        return ag.data_hora_inicio.startsWith(dataSelecionada);
    });

    if (ocupadosNoDia.length === 0) {
        listaOcupados.innerHTML = '<li style="color: var(--primary-color);">Nenhum horário ocupado. Quadra totalmente livre!</li>';
    } else {
        listaOcupados.innerHTML = '';
        ocupadosNoDia.forEach(function(ag) {
            const horaInicio = ag.data_hora_inicio.split('T')[1].substring(0, 5);
            const horaFim = ag.data_hora_fim.split('T')[1].substring(0, 5);
            
            const li = document.createElement('li');
            li.textContent = 'Das ' + horaInicio + ' às ' + horaFim;
            li.style.marginBottom = '0.3rem';
            listaOcupados.appendChild(li);
        });
    }
    containerOcupados.classList.remove('escondido');
}

function gerarComprovante(quadra, data, inicio, fim) {
    const dataFormatada = data.split('-').reverse().join('/'); 

    divStatus.innerHTML = 
        '<div style="border: 2px dashed #0056b3; padding: 20px; margin-top: 20px; background: #f8f9fa; border-radius: 8px; text-align: center;">' +
            '<h2 style="color: #0056b3; margin-bottom: 15px;">🎟️ Ticket de Reserva</h2>' +
            '<p><strong>Espaço:</strong> ' + quadra + '</p>' +
            '<p><strong>Data:</strong> ' + dataFormatada + '</p>' +
            '<p><strong>Horário:</strong> ' + inicio + ' às ' + fim + '</p>' +
            '<p style="font-size: 0.9em; color: #555; margin-top: 15px;">Tire um print ou imprima este comprovante para apresentar no local.</p>' +
            '<button onclick="window.print()" style="margin-top: 10px; padding: 8px 16px; background: #0056b3; color: white; border: none; border-radius: 4px; cursor: pointer;">🖨️ Imprimir</button>' +
        '</div>';
        
    divStatus.className = ''; 
}

formAgendamento.addEventListener('submit', async function(e) {
    e.preventDefault();
    limparStatus();

    const quadra_id = document.getElementById('select-quadra').value;
    const data = document.getElementById('data-agendamento').value;
    const hora_inicio = document.getElementById('hora-inicio').value;
    const hora_fim = document.getElementById('hora-fim').value;

    const data_hora_inicio = data + 'T' + hora_inicio + ':00';
    const data_hora_fim = data + 'T' + hora_fim + ':00';

    const objInicio = new Date(data_hora_inicio);
    const objFim = new Date(data_hora_fim);
    
    const diffMinutos = (objFim - objInicio) / (1000 * 60);

    if (diffMinutos <= 0) {
        mostrarStatus('A hora de término deve ser no futuro.', 'erro');
        return;
    }

    if (diffMinutos < 30) {
        mostrarStatus('O tempo mínimo de reserva é de 30 minutos.', 'erro');
        return;
    }

    if (diffMinutos > 120) {
        mostrarStatus('Você só pode reservar a quadra por no máximo 2 horas.', 'erro');
        return;
    }

    try {
        const resposta = await fetch(API_URL + '/agendamentos/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token 
            },
            body: JSON.stringify({
                quadra_id: parseInt(quadra_id),
                data_hora_inicio: data_hora_inicio,
                data_hora_fim: data_hora_fim
            })
        });

        if (resposta.ok) {
            const nomeQuadra = selectQuadra.options[selectQuadra.selectedIndex].text;
            
            formAgendamento.reset();
            containerOcupados.classList.add('escondido');
            selectQuadra.dispatchEvent(new Event('change'));
            
            gerarComprovante(nomeQuadra, data, hora_inicio, hora_fim);
        } else {
            const erroData = await resposta.json();
            mostrarStatus(erroData.detail || 'Erro ao agendar.', 'erro');
        }
    } catch (error) {
        mostrarStatus('Falha na comunicação com o servidor.', 'erro');
    }
});

carregarQuadras();