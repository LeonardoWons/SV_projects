function getQueryParameter(param) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

window.onload = function() {
    var leftOption = getQueryParameter('left_option') || 'Nenhuma peça';
    var rightOption = getQueryParameter('right_option') || 'Nenhuma peça';

    document.getElementById('imageSelectLeft').value = leftOption;
    document.getElementById('imageSelectRight').value = rightOption;
    showImage('left');
    showImage('right');
};

function showImage(position) {
    var select = document.getElementById('imageSelect' + capitalizeFirstLetter(position));
    var selectedOption = select.options[select.selectedIndex];
    var imageSrc = selectedOption.getAttribute('data-image');
    document.getElementById('selectedImage' + capitalizeFirstLetter(position)).src = imageSrc;
    document.getElementById('selectedImage' + capitalizeFirstLetter(position)).alt = "Imagem " + imageSrc;
}



function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}
