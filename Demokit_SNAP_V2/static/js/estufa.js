document.addEventListener("DOMContentLoaded", () => {

                const chart = echarts.init(document.getElementById('grafico'));

                let variavelAtual = "value_temp";

                let historicoCompleto = [];   // guarda todos os dados
                let dadosGrafico = [];

                const nomes = {
                    value_temp: "Temperatura Interna",
                    value_humid: "Umidade Interna",
                    s24ASD_temperature: "Temperatura S24",
                    s24ASD_humidity: "Umidade S24",
                    s24ASD_dewpoint: "Dew Point S24"
                };

                const unidades = {
                    value_temp: "°C",
                    value_humid: "%",
                    s24ASD_temperature: "°C",
                    s24ASD_humidity: "%",
                    s24ASD_dewpoint: "°C"
                };

                chart.setOption({
                    tooltip: { trigger: 'axis' },
                    xAxis: { type: 'time' },
                    yAxis: { type: 'value' },
                    dataZoom: [
                        { type: 'inside' },
                        { type: 'slider' }
                    ],
                    series: [{
                        name: nomes[variavelAtual],
                        type: 'line',
                        smooth: true,
                        data: []
                    }]
                });

                // 🔹 Carregar histórico inicial
                function carregarHistoricoInicial() {
                    fetch('/api/history/estufa')
                        .then(res => res.json())
                        .then(data => {

                            historicoCompleto = data;

                            reconstruirGrafico();
                        });
                }

                function reconstruirGrafico() {

                    dadosGrafico = historicoCompleto.map(item => {
                        return [new Date(item.timestamp), item[variavelAtual]];
                    });

                    chart.setOption({
                        series: [{
                            name: nomes[variavelAtual],
                            data: dadosGrafico
                        }]
                    });
                }

                // 🔌 Socket tempo real
                var socket = io.connect('http://' + document.domain + ':' + location.port + '/');

                socket.on('sensor_data', function(data) {

                    historicoCompleto.push(data);

                    if (historicoCompleto.length > 200) {
                        historicoCompleto.shift();
                    }

                    reconstruirGrafico();
                    atualizarCaixas(data);
                });

                // 🔄 Troca variável
                document.getElementById("variavelSelect").addEventListener("change", function() {
                    variavelAtual = this.value;
                    reconstruirGrafico();  // NÃO limpa histórico
                });

                function atualizarCaixas(data) {

                    const campos = [
                        "value_temp",
                        "value_humid",
                        "s24ASD_temperature",
                        "s24ASD_humidity",
                        "s24ASD_dewpoint"
                    ];

                    for (let i = 0; i < campos.length; i++) {

                        const box = document.getElementById(`valor${i+1}`);
                        const chave = campos[i];

                        if (data[chave] !== undefined) {
                            box.innerText = data[chave] + " " + unidades[chave];
                        } else {
                            box.innerText = "--";
                        }
                    }
                }

                carregarHistoricoInicial();

            });