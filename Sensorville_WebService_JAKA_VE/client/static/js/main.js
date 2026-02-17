$(document).ready(function() {

    // Função para atualizar as bordas dos elementos cruz e play
    function updateBorders(data) {
        // Borda verde se achou_cruz ou achou_play for True
        $('#cruz').toggleClass('green-border', data.achou_cruz);
        $('#play').toggleClass('green-border', data.achou_play);

        // Borda vermelha se VE_error for True
        $('#cruz, #play').toggleClass('red-border', data.VE_error);
    }

    // Função para atualizar as cores dos círculos
    function updateCircles(data) {
        // Atualiza cores dos círculos da cruz
        $('#cruz_circle1').css('background-color', data.color_cruz_circle1);
        $('#cruz_circle2').css('background-color', data.color_cruz_circle2);
        $('#cruz_circle3').css('background-color', data.color_cruz_circle3);
        $('#cruz_circle4').css('background-color', data.color_cruz_circle4);

        // Atualiza cores dos círculos do play
        $('#play_circle1').css('background-color', data.color_play_circle1);
        $('#play_circle2').css('background-color', data.color_play_circle2);
        $('#play_circle3').css('background-color', data.color_play_circle3);
    }

    // Função para atualizar os valores de torque nos círculos
    function updateValues(data) {
        console.log(data);
        // Atualiza os valores de torque para os círculos da cruz
        $('#cruz_circle1').text(data.value_cruz_circle1);
        $('#cruz_circle2').text(data.value_cruz_circle2);
        $('#cruz_circle3').text(data.value_cruz_circle3);
        $('#cruz_circle4').text(data.value_cruz_circle4);

        // Atualiza os valores de torque para os círculos do play
        $('#play_circle1').text(data.value_play_circle1);
        $('#play_circle2').text(data.value_play_circle2);
        $('#play_circle3').text(data.value_play_circle3);
    }

    // Função para buscar os dados do backend e atualizar a UI
    function fetchData() {
        $.ajax({
            url: '/data',
            method: 'GET',
            success: function(data) {
                updateBorders(data);
                updateCircles(data);
                updateValues(data);  // Atualiza os valores de torque
            },
            error: function(error) {
                console.error("Erro ao obter dados:", error);
            }
        });
    }

    // Atualiza a interface inicialmente
    fetchData();

    // Atualiza a interface a cada segundo
    setInterval(fetchData, 1000);
});
