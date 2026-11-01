const API_URL = window.location.port === '5500' ? 'http://127.0.0.1:8000' : window.location.origin;
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
const previsaoTempo = document.getElementById('previsao-tempo');

let agendamentosDaQuadraSelecionada = [];

function escaparHTML(value) {
    const span = document.createElement('span');
    span.textContent = String(value);
    return span.innerHTML.replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}

function imagemSegura(value) {
    if (!value) return '';
    try {
        const url = new URL(value, API_URL);
        return ['https:', 'http:'].includes(url.protocol) ? escaparHTML(url.href) : '';
    } catch { return ''; }
}

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
        
        const imgUrl = imagemSegura(q.imagem_url);

        card.innerHTML = 
            (imgUrl ? '<img loading="lazy" src="' + imgUrl + '" alt="Foto do espaço: ' + escaparHTML(q.nome) + '">' : '<div class="foto-pendente">Foto em breve</div>') +
            '<div class="info-quadra">' +
                '<h3>' + escaparHTML(q.nome) + '</h3>' +
                '<p><strong>Modalidade:</strong> ' + escaparHTML(q.tipo) + '</p>' +
                '<p><strong>Local:</strong> ' + escaparHTML(q.localizacao) + '</p>' +
            '</div>';
            
        gridDiv.appendChild(card);
        const comentarios = document.createElement('section');
        comentarios.className = 'comentarios-quadra';
        comentarios.innerHTML = '<h3>Comentários</h3><p>Carregando comentários…</p>';
        card.appendChild(comentarios);
        carregarComentarios(q.id, comentarios);
    });
}

async function carregarComentarios(quadraId, container) {
    try {
        const resposta = await fetch(API_URL + '/quadras/' + quadraId + '/comentarios/');
        if (!resposta.ok) throw new Error();
        const comentarios = await resposta.json();
        container.innerHTML = '<h3>Comentários</h3>';
        const lista = document.createElement('ul');
        lista.className = 'lista-comentarios';
        if (!comentarios.length) {
            const vazio = document.createElement('li'); vazio.textContent = 'Ainda não há comentários.'; lista.appendChild(vazio);
        }
        comentarios.forEach(c => {
            const item = document.createElement('li');
            const nome = document.createElement('strong'); nome.textContent = c.nome_usuario + ': ';
            const texto = document.createElement('span'); texto.textContent = c.texto;
            item.append(nome, texto);
            lista.appendChild(item);
        });
        container.appendChild(lista);
        if (token) {
            const form = document.createElement('form');
            form.innerHTML = '<label>Deixe seu comentário<textarea maxlength="1000" minlength="3" required></textarea></label><button class="btn-primario" type="submit">Publicar comentário</button>';
            form.addEventListener('submit', async e => {
                e.preventDefault(); const texto = form.querySelector('textarea').value;
                const r = await fetch(API_URL + '/quadras/' + quadraId + '/comentarios/', {method:'POST', headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({texto})});
                if (r.ok) carregarComentarios(quadraId, container);
            });
            container.appendChild(form);
        } else {
            const nota = document.createElement('p'); nota.textContent = 'Entre na sua conta para comentar.'; container.appendChild(nota);
        }
    } catch { container.innerHTML = '<h3>Comentários</h3><p>Não foi possível carregar os comentários.</p>'; }
}

const codigosTempo = {0:'Céu limpo',1:'Predominantemente limpo',2:'Parcialmente nublado',3:'Nublado',45:'Neblina',48:'Neblina',51:'Garoa leve',53:'Garoa',55:'Garoa forte',61:'Chuva leve',63:'Chuva',65:'Chuva forte',80:'Pancadas de chuva',81:'Pancadas de chuva',82:'Pancadas fortes',95:'Trovoadas'};
async function atualizarPrevisao() {
    const data = inputData.value;
    if (!data) { previsaoTempo.textContent = 'Selecione uma data para consultar a previsão do tempo em Potim.'; return; }
    previsaoTempo.textContent = 'Consultando a previsão do tempo…';
    try {
        const url = new URL('https://api.open-meteo.com/v1/forecast');
        url.search = new URLSearchParams({latitude:'-22.833',longitude:'-45.255',daily:'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',timezone:'America/Sao_Paulo',forecast_days:'16'});
        const resposta = await fetch(url); if (!resposta.ok) throw new Error();
        const dados = await resposta.json(); const indice = dados.daily.time.indexOf(data);
        if (indice < 0) { previsaoTempo.textContent = 'A previsão para essa data ainda não está disponível. Consulte novamente mais perto do dia.'; return; }
        previsaoTempo.textContent = '🌤️ Previsão em Potim: ' + (codigosTempo[dados.daily.weather_code[indice]] || 'Condição variável') + ', mínima de ' + Math.round(dados.daily.temperature_2m_min[indice]) + '°C e máxima de ' + Math.round(dados.daily.temperature_2m_max[indice]) + '°C. Chance máxima de chuva: ' + (dados.daily.precipitation_probability_max[indice] ?? '—') + '%. Fonte: Open-Meteo. Previsão sujeita a mudanças.';
    } catch { previsaoTempo.textContent = 'Não foi possível consultar a previsão agora. Tente novamente mais tarde.'; }
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

inputData.addEventListener('change', () => { atualizarListaOcupados(); atualizarPrevisao(); });

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
        '<div style="border: 2px dashed #0056b3; padding: 20px; margin-top: 40px; margin-bottom: 40px; background: #f8f9fa; border-radius: 8px; text-align: center;">' +
            '<h2 style="color: #0056b3; margin-bottom: 15px;">🎟️ Ticket de Reserva</h2>' +
            '<p><strong>Espaço:</strong> ' + escaparHTML(quadra) + '</p>' +
            '<p><strong>Data:</strong> ' + dataFormatada + '</p>' +
            '<p><strong>Horário:</strong> ' + inicio + ' às ' + fim + '</p>' +
            '<p style="font-size: 0.9em; color: #555; margin-top: 15px;">Tire um print ou imprima este comprovante para apresentar no local.</p>' +
            '<button onclick="window.print()" style="margin-top: 10px; padding: 8px 16px; background: #0056b3; color: white; border: none; border-radius: 4px; cursor: pointer;">🖨️ Imprimir</button>' +
        '</div>';
        
    divStatus.className = ''; 
    
    // Move o ticket para o final absoluto da página (filho direto do body)
    document.body.appendChild(divStatus);
    
    // Rola a página automaticamente para o fundo para o cidadão ver o ticket
    window.scrollTo(0, document.body.scrollHeight);
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
