document.addEventListener("DOMContentLoaded", () => {

    const chart = echarts.init(document.getElementById('grafico'));

    let variavelAtual = "qm30_v_mm_x";
    let historicoCompleto = [];
    let limiteCuidado = null;
    let limiteCritico = null;

    const campos = [
        "qm30_v_mm_x",
        "qm30_hf_a_x",
        "qm30_v_mm_y",
        "qm30_hf_a_y",
        "qm30_v_mm_z",
        "qm30_hf_a_z",
        "value_qm30_temp",
        "value_b22_status",
        "value_b22_peca",
        "s15cct_value"
    ];
    const nomes = {
        qm30_v_mm_x: "Vibração X",
        qm30_hf_a_x: "Alta Frequência X",
        qm30_v_mm_y: "Vibração Y",
        qm30_hf_a_y: "Alta Frequência Y",
        qm30_v_mm_z: "Vibração Z",
        qm30_hf_a_z: "Alta Frequência Z",
        value_qm30_temp: "Temperatura QM30",
        value_b22_status: "Status B22",
        value_b22_peca: "Peça B22",
        s15cct_value: "S15CCT"
    };

    chart.setOption({
        tooltip: { trigger: 'axis' },

        dataZoom: [
            { type: 'inside' },
            { type: 'slider' }
        ],

        xAxis: { type: 'time' },
        yAxis: { type: 'value' },

        visualMap: {
            show: false,
            dimension: 1,
            pieces: []   // começa vazio
        },

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

    carregarLimitesCNC(variavelAtual);

    function carregarLimitesCNC(variavel) {

        fetch(`/api/limites/cnc/${variavel}`)
            .then(res => res.json())
            .then(data => {

                limiteCuidado = data.min;
                limiteCritico = data.max;

                document.getElementById("valorCuidado").innerText = limiteCuidado;
                document.getElementById("valorCritico").innerText = limiteCritico;

                atualizarLinhasCNC();
            });
    }

    function atualizarLinhasCNC() {

        if (limiteCuidado === null || limiteCritico === null) return;

        chart.setOption({
            series: [{
                markLine: {
                    silent: true,
                    data: [
                        {
                            yAxis: limiteCuidado,
                            lineStyle: { color: '#ff9800', width: 2 },
                            label: { formatter: 'Cuidado: ' + limiteCuidado }
                        },
                        {
                            yAxis: limiteCritico,
                            lineStyle: { color: '#f44336', width: 2 },
                            label: { formatter: 'Crítico: ' + limiteCritico }
                        }
                    ]
                }
            }],
            visualMap: {
                pieces: [
                    {
                        gt: limiteCritico,
                        color: '#f44336'
                    },
                    {
                        gt: limiteCuidado,
                        lte: limiteCritico,
                        color: '#ff9800'
                    }
                ]
            }
        }, false);
    }

    // 🔹 Carrega histórico inicial
    function carregarHistoricoInicial() {
        fetch('/api/history/cnc')
            .then(res => res.json())
            .then(data => {

                historicoCompleto = data;

                reconstruirGrafico();
                atualizarCaixas(data[data.length - 1]);
            });
    }

    function reconstruirGrafico() {

        const dadosGrafico = historicoCompleto.map(item => {
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

        if (historicoCompleto.length > 300) {
            historicoCompleto.shift();
        }

        reconstruirGrafico();
        atualizarCaixas(data);
    });

    document.getElementById("variavelSelect").addEventListener("change", function() {
        variavelAtual = this.value;

        chart.setOption({
            series: [{ data: [] }]
        });

        carregarLimitesCNC(variavelAtual);

    });

    function atualizarCaixas(data) {

        for (let i = 0; i < campos.length; i++) {

            const box = document.getElementById(`valor${i+1}`);
            const chave = campos[i];

            if (data && data[chave] !== undefined) {
                box.innerText = data[chave];
            } else {
                box.innerText = "--";
            }
        }
    }

    var socket = io();

    socket.on("qm30_training_status", function(data){

        document.getElementById("qm30Remain").innerText = data.remain;

        if(data.finalizado){
            alert("Treinamento QM30 finalizado");
        }

    });

    carregarHistoricoInicial();

    document.querySelectorAll(".acao-btn").forEach(btn => {

        btn.addEventListener("click", function() {

            const indice = this.dataset.indice;
            const variavel = campos[indice];

            fetch("/api/executar_acao_cnc", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    variavel: variavel
                })
            });

        });

    });

});

function iniciarTreinamento(){
    fetch("/api/executar_acao_cnc", {
        method: "POST"
    })
    .then(r => r.json())
    .then(data => {
        console.log(data);
    });
}
