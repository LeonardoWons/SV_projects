import time
import tkinter as tk
from PIL import Image, ImageTk
import threading
import subprocess
import pyautogui as gui
from pymodbus.client import ModbusSerialClient
import psutil
import json
import socket

# Database reading functions / Funções de leitura do banco de dados
from database_rfid import insert_data, search_badge
from connect_to_sql_rfid import test_rfid_connection, collect_rfids
from collect_data import get_data
from database import update_sql, get_sql_size, get_10_sql, delete_x_sql
from connect_to_sql_john import send_to_sql_john, test_sql_connection

from rfid import read_rfid_card

serial_lock = threading.Lock()  # Lock for serial access / Trava para o acesso serial
supervisor_mode = False  # Supervisor mode variable / Variável para o modo supervisor
global_badge = ""
locked_tugger = True
root = None
data = None
connected = False


jd_green = "#367c2b"

try:
    initial_client_lock_block = ModbusSerialClient(method="rtu", port="COM2", baudrate=19200, timeout=1, parity="N", stopbits=1, bytesize=8)
    initial_client_lock_block.connect()
    initial_client_lock_block.write_register(address=40400, value=0, slave=4)
    initial_client_lock_block.close()
    b22_block_on = True

except Exception as o:
    print(f"Error in initial block: {o}")


# Function to refresh RFID database / Função para atualizar o banco de dados RFID
def refresh_db_rfid():
    if test_rfid_connection():
        rfid_data = collect_rfids()
        if rfid_data != "erro":
            insert_data(rfid_data)  # rfid_data needs to be a list / rfid_data precisa ser uma lista
            return "Atualizado com sucesso"
        else:
            return "Erro na coleta dos cartões"
    else:
        return "Sem conexão com Database"


# Function to refresh database via button / Função para atualizar o banco de dados via botão
def refresh_db_rfid_button():
    button_refresh.configure(state="disabled")  # Disable button during refresh / Desabilitar botão durante o refresh
    refresh_return = refresh_db_rfid()
    if refresh_return == "Atualizado com sucesso":
        label_refresh.configure(fg=jd_green)
    else:
        label_refresh.configure(fg="red")
    label_refresh.configure(text=refresh_return)
    button_refresh.configure(state="normal")  # Re-enable button / Reativar botão


# Function to load images / Função para carregar imagens
def load_image(path, size):
    image = Image.open(path)
    image = image.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


# Function to read RFID and validate badge / Função para leitura do RFID e validação do crachá
def rfid_reader():

    global global_badge
    global locked_tugger
    global root

    while locked_tugger:
        badge_read = read_rfid_card()
        if badge_read[0] == ":":
            new_badge_read = badge_read.replace(":)0", "")
        else:
            new_badge_read = "1" + badge_read
        badge_found = search_badge(new_badge_read)

        if badge_found:

            message_label.configure(fg=jd_green)
            message_label.configure(text="Crachá validado com sucesso! Liberando acesso .")
            time.sleep(1)
            message_label.configure(text="Crachá validado com sucesso! Liberando acesso ..")
            time.sleep(1)
            message_label.configure(text="Crachá validado com sucesso! Liberando acesso ...")
            time.sleep(1)
            if supervisor_mode:
                global_badge = "supervisor-" + new_badge_read
            else:
                global_badge = new_badge_read

            locked_tugger = False
            root.after(0, hide_gui())

            label_refresh.configure(text="")
            message_label.configure(fg="black")
            message_label.configure(text="Ligue o equipamento, depois passe o crachá no local identificado pela imagem abaixo para habilitar o equipamento")
            
        else:
            message_label.configure(fg="red")

            message_label.configure(text="Crachá não validado. Contate seu supervisor.")
            time.sleep(1)
            message_label.configure(text="Crachá não validado. Contate seu supervisor..")
            time.sleep(1)
            message_label.configure(text="Crachá não validado. Contate seu supervisor...")
            time.sleep(1)
            label_refresh.configure(text="")
            message_label.configure(fg="black")
            message_label.configure(
                text="Ligue o equipamento, depois passe o crachá no local identificado pela imagem abaixo para habilitar o equipamento")


# Function to enable via supervisor / Função para habilitar por supervisor
def supervisor():
    global supervisor_mode

    if not supervisor_mode:
        label_refresh.configure(text="")
        message_label.configure(
            text="Supervisor, ligue o equipamento, depois passe o crachá no local identificado pela imagem abaixo para habilitar o equipamento")
        button_label.configure(
            text="Esteja ciente que ao executar esta ação,"
                 "você se responsabiliza pelo uso do equipamento pelo funcionário.")
        button.configure(text="Cancelar operação")
        supervisor_mode = True
    else:
        label_refresh.configure(text="")
        message_label.configure(
            text="Ligue o equipamento, depois passe o crachá no local identificado pela imagem abaixo para habilitar o equipamento")
        button_label.configure(
            text="Toque no botão para habilitar com o crachá do supervisor")
        button.configure(text="Habilitar por supervisor")
        supervisor_mode = False


# GUI Function to run the Tkinter window / Função GUI para rodar a janela Tkinter
def gui_rf_id_interface():
    global message_label, button_label, button, root, button_refresh, label_refresh, rfid

    if root is None:
        # Create the main window / Criação da janela principal
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.protocol("WM_DELETE_WINDOW", lambda: None)  # Previne fechamento acidental
        root.wm_attributes('-topmost', True)  # Manter a janela no topo

        # Set the window width and height / Definir a largura e altura da janela
        window_width = root.winfo_screenwidth()
        window_height = root.winfo_screenheight()

        # Main frame / Frame principal
        frame = tk.Frame(root)
        frame.pack()

        canvas = tk.Canvas(frame, width=window_width, height=window_height, bd=0, highlightthickness=0, bg="#e7e7e7")
        canvas.pack()

        # Load images / Carregar imagens
        screen_div_7 = round(window_height / 7)
        sticker_height = round((window_height / 7) * 2)

        header = load_image(r"C:\Users\PPC_JD\Telemetry\fotos\header.png", (window_width, screen_div_7))
        sv_logo = load_image(r"C:\Users\PPC_JD\Telemetry\fotos\sv.png", (screen_div_7, screen_div_7))
        sticker = load_image(r"C:\Users\PPC_JD\Telemetry\fotos\sticker.png", (sticker_height, sticker_height))

        root.header = header
        root.sv_logo = sv_logo
        root.sticker = sticker

        canvas.create_image(0, 0, image=header, anchor="nw")
        canvas.create_image(window_width - (window_height * 0.15) // 2, 0, image=sv_logo, anchor="n")

        font_size = round(window_height * 0.03)

        # Create Label with text in Portuguese and English / Criar Label com texto em português e inglês
        message_label = tk.Label(
            root, text="Ligue o equipamento, depois passe o crachá no local identificado pela imagem abaixo para habilitar o equipamento",
            font=("Helvetica", font_size), bg="#e7e7e7", fg="black", wraplength=(window_width // 10) * 9)
        message_label.place(relx=0.5, y=screen_div_7 * 2.25, anchor=tk.CENTER)

        # Create badge image / Criar imagem do crachá
        canvas.create_image(window_width / 2, screen_div_7 * 4, image=sticker, anchor=tk.CENTER)

        # Supervisor button / Botão para o supervisor
        button_label = tk.Label(
            root, text="Toque no botão para habilitar com o crachá do supervisor",
            font=("Helvetica", int(font_size // 1.5)), bg="#e7e7e7", fg="black", wraplength=(window_width // 10) * 9)
        button_label.place(relx=0.5, y=screen_div_7 * 5.6, anchor=tk.CENTER)

        button = tk.Button(
            root, text="Habilitar por supervisor", font=("Helvetica", int(font_size // 1.5)),
            bg="#ffde00", command=supervisor)
        button.place(relx=0.5, y=screen_div_7 * 5.5 + screen_div_7 / 2, anchor=tk.CENTER)

        # Button to refresh the database / Botão para atualizar o banco de dados
        button_refresh = tk.Button(
            root, text="Refresh DataBase", font=("Helvetica", int(font_size // 1.5)), bg="#ffde00",
            command=refresh_db_rfid_button)
        button_refresh.place(relx=0.9, y=screen_div_7 * 1.25, anchor=tk.CENTER)

        # Label to display refresh result / Label para exibir o resultado do refresh
        label_refresh = tk.Label(
            root, text="",
            font=("Helvetica", int(font_size // 2)), bg="#e7e7e7", fg=jd_green)
        label_refresh.place(relx=0.5, y=screen_div_7 * 1.3, anchor=tk.CENTER)

    show_gui()


def hide_gui():
    if root:
        root.withdraw()  # Esconde a janela, mas a mantém pronta para reexibir


def show_gui():
    global root
    if root:
        root.deiconify()


def get_computer_name():
    try:
        # Obtém o nome do host do computador
        var_computer_name = socket.gethostname()
        return var_computer_name
    except Exception as e:
        #print(f"Erro ao obter o nome do computador: {e}")
        return None


computer_name = get_computer_name()


# Main function that includes database communication and equipment control logic
# Função principal que inclui a lógica de comunicação com o banco de dados e controle do equipamento
def collect():
    global locked_tugger
    global global_badge
    global data
    global connected

    while True:

        with serial_lock:
            data = get_data()

        # Verifica se precisa bloquear rebocador / Check if the tugger needs to be blocked
        if data["tugger_status"] == "0":
            locked_tugger = True

        data['badge'] = global_badge

        data['tugger_id'] = computer_name
        data['internet_connected'] = connected

        json_str = json.dumps(data, sort_keys=True, default=str)
        json_data = json.loads(json_str)

        try:
            update_sql(
                json_data["tugger_id"], json_data["date_time"],
                json_data["gps_latitude"], json_data["gps_longitude"], json_data["gps_altitude"],
                json_data["gps_signal_quality"], json_data["gps_satellite_count"],
                json_data["gps_pdop"], json_data["gps_hdop"], json_data["gps_vdop"],
                json_data["gps_speed"], json_data["gps_direction"],
                json_data["tugger_status"], json_data["current_value"], json_data["badge"],
                json_data["internet_connected"], json_data["reverse_gear_status"]
            )

        except Exception as b:
            print(f"error in Main: {b}")


def connect_and_send_jd():
    global connected

    while True:
        try:
            connected = test_sql_connection()

            sql_size = get_sql_size()

            if connected and sql_size > 10:
                sent_count = send_to_sql_john(get_10_sql())

                if sent_count > 0:
                    delete_x_sql(sent_count)
            else:
                pass

        except Exception as b:
            print(f"Erro in SQL connection test: {b}")
            connected = False

        time.sleep(1)


def locked_tugger_logic():

    global locked_tugger
    global b22_block_on
    global global_badge

    while True:
        if not locked_tugger and b22_block_on:
            with serial_lock:
                try:
                    client_lock_unlock = ModbusSerialClient(method="rtu", port="COM2", baudrate=19200, timeout=1,
                                                         parity="N", stopbits=1, bytesize=8)
                    client_lock_unlock.connect()
                    client_lock_unlock.write_register(address=40400, value=1, slave=4)
                    client_lock_unlock.close()

                    b22_block_on = False

                except Exception as o:
                    print(f"Error in block: {o}")

        if locked_tugger:
            try:
                root.after(0, show_gui())
            except:
                pass
            if not b22_block_on:
                with serial_lock:
                    try:
                        client_lock_block = ModbusSerialClient(method="rtu", port="COM2", baudrate=19200, timeout=1,
                                                         parity="N", stopbits=1, bytesize=8)
                        client_lock_block.connect()
                        client_lock_block.write_register(address=40400, value=0, slave=4)
                        client_lock_block.close()
                        b22_block_on = True

                    except Exception as o:
                        print(f"Error in block: {o}")
            global_badge = ""
            rfid_reader()


# Function for controlling the camera via Modbus / Função para controle da câmera via Modbus
def camera_control():
    slave_re_status = 3
    address_re_status_value_pin4 = 40002
    global data

    while True:
        time.sleep(0.4)
        if not b22_block_on and not locked_tugger:
            """with serial_lock:
                try:
                    client2 = ModbusSerialClient(method="rtu", port="COM2", baudrate=19200, timeout=1, parity="N", stopbits=1, bytesize=8)
                    client2.connect()

                    read2 = client2.read_holding_registers(address_re_status_value_pin4, 2, slave_re_status)

                    if read2.isError():
                        continue

                    status = read2.registers[0]
                    client2.close()

                except Exception as e:
                    print(e)
                    continue
            """
            if data is not None:

                status = data["reverse_gear_status"]

                camera_open = any(proc.info['name'] == 'WindowsCamera.exe' for proc in psutil.process_iter(['name']))

                if status == "1" and not camera_open:
                    subprocess.Popen("START /MAX explorer shell:appsfolder\\Microsoft.WindowsCamera_8wekyb3d8bbwe!App", shell=True)
                    gui.sleep(1)
                    gui.hotkey('shift', 'win', 'enter')

                elif status == "0" and camera_open:
                    subprocess.run(['taskkill', '/IM', 'WindowsCamera.exe', '/F'])


def start_gui():
    gui_rf_id_interface()
    root.mainloop()


# Start threads to run main and camera control / Iniciar threads para rodar main e controle da câmera
collect = threading.Thread(target=collect, daemon=True)
thread_gui = threading.Thread(target=start_gui, daemon=True)
thread_camera = threading.Thread(target=camera_control, daemon=True)
connect_send_jd = threading.Thread(target=connect_and_send_jd, daemon=True)
thread_locked_tugger = threading.Thread(target=locked_tugger_logic, daemon=True)


# Start the threads / Iniciar as threads
collect.start()
thread_gui.start()
thread_camera.start()
connect_send_jd.start()
thread_locked_tugger.start()

# Wait for the threads to finish (which won't happen due to the infinite loop) /
# Esperar as threads terminarem (o que não vai acontecer devido ao loop infinito)
collect.join()
thread_gui.join()
thread_camera.join()
connect_send_jd.join()
thread_locked_tugger.join()
