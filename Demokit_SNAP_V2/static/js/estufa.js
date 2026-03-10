document.addEventListener("DOMContentLoaded", () => {

                const chart = echarts.init(document.getElementById('grafico'));

                let variavelAtual = "value_temp";
                let historicoCompleto = [];
                let limiteMin = null;
                let limiteMax = null;

                carregarLimites("estufa", variavelAtual);

                const campos = [
                        "value_temp",
                        "value_humid",
                        "s24ASD_temperature",
                        "s24ASD_humidity",
                        "s24ASD_dewpoint"
                ];


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

                    dataZoom: [
                        { type: 'inside' },
                        { type: 'slider' }
                    ],

                    xAxis: { type: 'time' },
                    yAxis: { type: 'value' },

                    series: [{
                        name: nomes[variavelAtual],
                        type: 'line',
                        smooth: true,
                        data: [],
                        markLine: {
                            silent: true,
                            data: []
                        }
                    }]
                });

                function carregarLimites(setor, variavel) {

                    fetch(`/api/limites/${setor}/${variavel}`)
                        .then(res => res.json())
                        .then(data => {

                            limiteMin = data.min;
                            limiteMax = data.max;

                            // Atualiza inputs
                            document.getElementById("limiteMin").value = limiteMin ?? "";
                            document.getElementById("limiteMax").value = limiteMax ?? "";

                            atualizarLimitesNoGrafico();
                        });
                }


                function atualizarLimitesNoGrafico() {

                    let linhas = [];

                    if (limiteMin !== null) {
                        linhas.push({
                            yAxis: limiteMin,
                            lineStyle: { color: '#2196F3', width: 2 },
                            label: { formatter: 'Min: ' + limiteMin }
                        });
                    }

                    if (limiteMax !== null) {
                        linhas.push({
                            yAxis: limiteMax,
                            lineStyle: { color: '#f44336', width: 2 },
                            label: { formatter: 'Max: ' + limiteMax }
                        });
                    }

                    chart.setOption({
                        series: [{
                            markLine: {
                                silent: true,
                                data: linhas
                            }
                        }]
                    }, false);
                }

                document.getElementById("aplicarLimites").addEventListener("click", function () {

                    const minInput = document.getElementById("limiteMin").value;
                    const maxInput = document.getElementById("limiteMax").value;

                    limiteMin = minInput !== "" ? parseFloat(minInput) : null;
                    limiteMax = maxInput !== "" ? parseFloat(maxInput) : null;

                    atualizarLimitesNoGrafico();

                    fetch("/api/limites", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                                setor: "estufa",          // cnc / estufa / tanque
                            variavel: variavelAtual,    // ex: value_temp
                            min: limiteMin,
                            max: limiteMax
                        })
                    });
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
                    // limpa dados se necessário
                    chart.setOption({
                        series: [{ data: [] }]
                    });
                    reconstruirGrafico();
                    carregarLimites("estufa", variavelAtual);
                });

                function atualizarCaixas(data) {

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