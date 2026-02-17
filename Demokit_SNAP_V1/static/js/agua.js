document.addEventListener("DOMContentLoaded", () => {
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/');
    socket.on('sensor_data', function(data) {
        document.getElementById('sensor1').innerText = (100 - data.q4x).toFixed(1);
        document.getElementById('lazer').style.clipPath = `inset(0 ${(100-data.q4x)}% 0 0)`;

        document.getElementById('water-level').style.height = (100 - data.q4x) + '%';

        const timestamp = new Date();
        myChart.data.labels.push(timestamp);
        myChart.data.datasets[0].data.push((100 - data.q4x));

        console.log(data.q4x);

        if (myChart.data.labels.length > 20) {
            myChart.data.labels.shift();
            myChart.data.datasets[0].data.shift();
        }

        myChart.update();

    });

    // Configuração do gráfico
    const ctx = document.getElementById('myChart').getContext('2d');
    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Nivel do tank',
                data: [],
                borderColor: 'rgba(251, 196, 0, 1)',
                borderWidth: 1,
                fill: false,
                tension: 0.2,
                pointRadius: 10
            }]
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'second', // Mostrar marcas de tempo em segundos
                        displayFormats: {
                            second: 'hh:mm:ss' // Formato de exibição para cada ponto de tempo
                        }
                    },
                    ticks: {
                        autoSkip: false, // Mostrar todas as marcas de tempo
                        maxRotation: 90,
                        minRotation: 45,
                        font: {
                            size: 10 // Fonte do eixo x
                        }
                    }
                },
                y: {
                    suggestedMin: 0,
                    suggestedMax: 110,
                    title: {
                        display: true,
                        text: 'Valor'
                    },
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 20 // Fonte do eixo y
                        },
                        stepSize: 10,
                        padding: 10
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        font: {
                            size: 15 // Aumentar a fonte da legenda
                        }
                    }
                },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    font: {
                        size: 10,
                    },
                    formatter: (value) => value.toFixed(0)
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    // Buscar dados do banco de dados e atualizar o gráfico
    fetch('/api/data/agua')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(d => new Date(d.timestamp));
            const values = data.map(d => d.value);

            const limitedLabels = labels.slice(-20);
            const limitedValues = values.slice(-20);

            myChart.data.labels = limitedLabels;
            myChart.data.datasets[0].data = limitedValues;
            myChart.update();
        });
});