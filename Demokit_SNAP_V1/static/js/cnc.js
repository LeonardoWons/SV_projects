// Função para buscar dados de tempo médio por peça
function fetchTempoMedioPeca() {
    fetch('/api/data/tempo_medio_peca')
        .then(response => response.json())
        .then(data => {
            let percentual_diferenca = data.percentual_diferenca; // Mudando para 'let'

            updateIndicator('tempo', percentual_diferenca, 10);
        })
        .catch(error => console.error('Error fetching tempo medio peca data:', error));
}

function fetchStatusDifference() {
    fetch('/api/data/status_difference')
        .then(response => response.json())
        .then(data => {
            const percentualDifference = data.percentual_difference;

            updateIndicator('status-difference', percentualDifference, 100);
        })
        .catch(error => console.error('Error fetching status difference data:', error));
}

function updateCircleColor(status) {
    const circle = document.getElementById('status-circle');

    if (status === 1) {
        circle.style.backgroundColor = 'green';
    } else {
        circle.style.backgroundColor = 'red';
    }
}

function updateIndicator(id, value, max) {
    const bar = document.getElementById(id + '-bar');
    const scale = document.getElementById(id + '-scale');
    const valueDisplay = document.getElementById(id + '-value');

    if (id == 'tempo'){

        valueDisplay.textContent = (value*10).toFixed(0) + '%';

        if (value > 10){
            value = 10;
        }
        bar.style.bottom = ((value*10) - 1) + '%'

        const marks = Array.from({ length: 11 }, (_, i) => (max - (max / 10) * i) + "p/s");
        scale.innerHTML = marks.map(mark => `<div>${mark}</div>`).join('');
    }
    else if (id == 'status-difference'){

        valueDisplay.textContent = (value).toFixed(0) + '%';

        if (value > 10){
            value = 10;
        }

        bar.style.bottom = (value - 1) + '%';

        const marks = Array.from({ length: 11 }, (_, i) => (max - (max / 10) * i) + "%");
        scale.innerHTML = marks.map(mark => `<div>${mark}</div>`).join('');
    }
    else{
        bar.style.bottom = (((value/max)*100) - 1).toFixed(0) + '%'
        valueDisplay.textContent = value;

        const marks = Array.from({ length: 11 }, (_, i) => (max - (max / 10) * i));
        scale.innerHTML = marks.map(mark => `<div>${mark}</div>`).join('');
    }
}

document.addEventListener("DOMContentLoaded", () => {
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/');
    socket.on('sensor_data', function(data) {
        updateIndicator('qm30_hf_a_z', data.qm30_hf_a_z, 65);
        updateIndicator('qm30_hf_a_x', data.qm30_hf_a_x, 65);

        updateIndicator('qm30_v_mm_z', data.qm30_v_mm_z, 65);
        updateIndicator('qm30_v_mm_x', data.qm30_v_mm_x, 65);

        updateIndicator('temperatura', data.value_qm30_temp, 300);
        updateCircleColor(data.value_b22_status);

    });

    setInterval(fetchTempoMedioPeca, 2000);
    fetchTempoMedioPeca();

    setInterval(fetchStatusDifference, 2000);
    fetchStatusDifference();
});
