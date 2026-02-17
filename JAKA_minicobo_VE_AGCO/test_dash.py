from flask import Flask, render_template, jsonify
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dados')
def dados():
    textos_img = [
        ['Data: 30/05', 'Resultado: OK', 'Inspeção: 10', 'Modelo: SV MADE'],
        ['Data: 30/05', 'Resultado: NOK', 'Inspeção: 5', 'Modelo: SV MADE'],
        ['Data: 30/05', 'Resultado: OK', 'Inspeção: 12', 'Modelo: SV MADE'],
        ['Data: 30/05', 'Resultado: OK', 'Inspeção: 8', 'Modelo: SV MADE']
    ]

    imagens = ['Parafuso 1.jpg', 'Parafuso 2.jpg', 'Parafuso 3.jpg', 'Parafuso 4.jpg']  # substitua por lógica real se necessário

    return jsonify({'textos': textos_img, 'imagens': imagens})

if __name__ == "__main__":
    app.run(debug=True)