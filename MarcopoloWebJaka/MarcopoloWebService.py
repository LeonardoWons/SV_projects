# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from flask import Flask, request, jsonify, render_template, url_for, redirect, flash

from pymodbus.client.sync import ModbusTcpClient

import sqlite3

# import jkrc


# Função para instalar pacotes
def install_packages():
    try:
        requirement_dir = os.path.join(os.path.dirname(__file__), 'AddOn_tools', 'requirement')
        # Instalar pyserial primeiro
        for filename in os.listdir(requirement_dir):
            if 'pyserial' in filename:
                package_path = os.path.join(requirement_dir, filename)
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_path])

        # Instalar pymodbus sem dependências
        for filename in os.listdir(requirement_dir):
            if 'pymodbus' in filename:
                package_path = os.path.join(requirement_dir, filename)
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_path, '--no-deps'])

        print("Instalação completa.")
    except subprocess.CalledProcessError as e:
        print("Falha na instalação de pacotes:", e)


def init_db():
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photos.db'))
    conn.text_factory = str
    cursor = conn.cursor()

    table = cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' 
                AND name='photos'; """).fetchall()

    if not table:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            side TEXT NOT NULL,
            filename TEXT NOT NULL) ''')

        photos = [
            ("Nenhuma peça", "lr", "nenhuma_peca.jpg"),
            ("Viaggio G8 sem auto falante", "lr", "viaggio_g8_sem_auto.jpg"),
            ("Viaggio G8 com auto falante", "right", "viaggio_g8_com_auto.jpg"),
            ("Viaggio G8 senior", "left", "viaggio_g8_senior.jpg"),
            ("Alça pega mão", "lr", "pega_mao.jpg"),
            ("Numerador poltrona", "right", "numerador.jpg"),
        ]

        cursor.executemany('''
            INSERT INTO photos (name, side, filename)
            VALUES (?, ?, ?)
            ''', photos)

        conn.commit()

    conn.close()


def get_db_connection():
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photos.db'))
    conn.text_factory = str  # Garante que estamos usando strings Unicode
    return conn


def get_photos(side):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, filename FROM photos WHERE side=? OR side='lr'", (side,))
    photos = cursor.fetchall()
    conn.close()
    return photos


def start_flask_app():
    # Caminhos absolutos para templates e arquivos estáticos
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client', 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client', 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # Configuração do cliente Modbus
    #modbus_host = '10.5.5.100'  # IP do robô
    #modbus_port = 502  # Porta padrão do Modbus TCP

    #client = ModbusTcpClient(modbus_host, port=modbus_port)

    @app.route('/')
    def home():
        #read = client.read_coils(40, 18)
        #print(read)
        #ead_result = client.read_coils(address=40, count=16)
        #trad = read_coils_jaka_translate(read_result)

        left_option = request.args.get('left_option', 'Nenhuma peça')
        right_option = request.args.get('right_option', 'Nenhuma peça')
        left_photos = get_photos('left')
        right_photos = get_photos('right')

        trad = ['left', 'right']
        return render_template('index.html', left_option=left_option, right_option=right_option,
                               left_msg=trad[0], right_msg=trad[1], left_photos=left_photos, right_photos=right_photos)

    @app.route('/submit', methods=['POST'])
    def submit():
        selected_option = request.form.get('selectedOption')
        side = request.form.get('side')
        unit_id = 1
        values = ['0'] * 8

        if selected_option != 'Nenhuma peça':
            opcoes = {"Numerador poltrona": 0, "Alça pega mão": 1, "Viaggio G8 senior": 2, "Viaggio G8 com auto": 3,
                      "Viaggio G8 sem auto": 4}
            a = opcoes[selected_option]
            values[a] = '1'

        left_option = request.form.get('left_option', 'Nenhuma peça')
        right_option = request.form.get('right_option', 'Nenhuma peça')

        if side == 'left':
            left_option = selected_option
            address = 48
        elif side == 'right':
            right_option = selected_option
            address = 40

        try:
            # Enviar comando Modbus para escrever múltiplas bobinas
            '''result = client.write_coils(address, values, unit=unit_id)

            if result.isError():
                if side == 'left':
                    return redirect(url_for('home', left_option=left_option, left_error="Falha no envio", right_option=right_option))
                elif side == 'right':
                    return redirect(url_for('home', left_option=left_option, right_option=right_option, right_error="Falha no envio"))

            read_result = client.read_coils(address=40, count=16)
            trad = read_coils_jaka_translate(read_result)
            '''
            trad = ['left', 'right']
            print(values, '\n', left_option, '\n', right_option, '\n', selected_option)
            return redirect(url_for('home', left_option=left_option, right_option=right_option, left_msg=trad[0], right_msg=trad[1]))

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    app.run(host='0.0.0.0', port=10007)  # Porta 10007


def read_coils_jaka_translate(traduzir):
    # preciso passar o resulto do client.read_coils e retornar status = [qual_peça_left_fazendo, qual_peça_left_fazendo]
    print(traduzir)
    return ['l', 'r']


if __name__ == '__main__':
    # install_packages()  # Instalar pacotes primeiro

    init_db()  # inicia o bd de fotos

    start_flask_app()  # Iniciar a aplicação Flask
