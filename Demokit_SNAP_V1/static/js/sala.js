document.addEventListener("DOMContentLoaded", () => {
    const ctx2 = document.getElementById('chart2').getContext('2d');

    // Configuração do gráfico de linhas
    let chart2 = new Chart(ctx2, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Temperatura',
                    borderColor: 'red',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    data: [],
                    fill: false,
                    pointStyle: 'circle',
                    pointRadius: 20,
                    pointHoverRadius: 10,

                },
                {
                    label: 'Umidade',
                    borderColor: 'blue',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    data: [],
                    fill: false,
                    pointStyle: 'triangle',
                    pointRadius: 20,
                    pointHoverRadius: 10
                }
            ]
        },
        options: {
            spanGaps: 1000 * 15,
            responsive: true,
            interaction: {
              mode: 'nearest',
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'second', // Mostrar marcas de tempo em segundos
                        displayFormats: {
                            second: 'mm:ss' // Formato de exibição para cada ponto de tempo
                        }
                    },
                    ticks: {
                        autoSkip: false, // Mostrar todas as marcas de tempo
                        maxRotation: 0,
                        major: {
                            enabled: true
                        },
                        font: {
                            size: 40 // Fonte do eixo x
                        },
                        padding: 30,
                    }
                },
                y: {
                    suggestedMin: 0,
                    suggestedMax: 110,
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 40 // Fonte do eixo y
                        },
                        stepSize: 10,
                        padding: 40,
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        font: {
                            size: 40 // Aumentar a fonte da legenda
                        },
                    }
                },
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
                },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    font: {
                        size: 40,
                    },
                    formatter: function(value) {
                        return typeof value === 'number' ? value.toFixed(0) : value;
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });


    // Função para buscar e atualizar os dados dos gráficos
    function fetchData() {
        fetch('/api/data/sala')
            .then(response => response.json())
            .then(data => {

                const labels = data.map(entry => new Date(entry.timestamp));
                const valuesTemp = data.map(entry => entry.temp);
                const valuesHumid = data.map(entry => entry.humid);;

                chart2.data.labels = labels;
                chart2.data.datasets[0].data = valuesTemp;
                chart2.data.datasets[1].data = valuesHumid;
                chart2.update();
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    var socket = io.connect('http://' + document.domain + ':' + location.port + '/');
    socket.on('sensor_data', function(data) {
        updateIndicator('temp', data.value_temp);
        updateIndicator('humid', data.value_humid);
    });

    fetchData();
    setInterval(fetchData, 1000); // Atualiza os gráficos a cada 1 segundo
});

function updateIndicator(id, value) {
    const valueDisplay = document.getElementById(id);
    if (id == 'temp'){
        valueDisplay.textContent = value + ' °C';
    }
    else{
        valueDisplay.textContent = value + ' %';
    }
}
