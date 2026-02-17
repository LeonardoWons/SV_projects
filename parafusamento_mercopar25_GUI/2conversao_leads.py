
"""
salvar_codigos_db.py
Lê arquivos .db, extrai códigos entre SHIFT e ENTER (da coluna especificada),
e salva os códigos únicos em um novo banco SQLite.
"""

"""
gerar_codigos_barras.py
Gera códigos de barras (Code128) a partir dos códigos salvos no banco codigos_extraidos.db
e salva cada um como uma imagem PNG.
"""

import os
import sqlite3
from barcode import Code128
from barcode.writer import ImageWriter

# --------- CONFIGURAÇÃO ----------
DB_FILES = [
    "keystrokes.db",
    "14-10.db",
    "15-10.db",
]
# índice da coluna onde estão os keystrokes (0 = primeira coluna).
# Você disse que precisa da coluna 2 -> use index 1
COLUMN_INDEX = 1

OUTPUT_DB = "codigos_extraidos.db"
OUTPUT_TABLE = "codigos"
# ---------------------------------

def get_table_names(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [r[0] for r in cur.fetchall()]

def extrair_codigos_de_linhas(linhas):
    codigos = []
    atual = []
    gravando = False

    for valor in linhas:
        # manter o valor original para juntar, mas comparar em uppercase para SHIFT/ENTER
        raw = "" if valor is None else str(valor)
        val_upper = raw.strip().upper()

        if val_upper == "SHIFT":
            atual = []
            gravando = True
            continue

        if val_upper == "ENTER":
            if gravando and atual:
                codigos.append("".join(atual))
            gravando = False
            atual = []
            continue

        if gravando:
            # acrescenta o texto tal qual (sem strip extra só pra evitar espaços laterais)
            # se quiser apenas o primeiro caractere: atual.append(raw.strip()[0])
            atual.append(raw.strip())

    return codigos

def ensure_output_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {OUTPUT_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        origem_db TEXT,
        origem_tabela TEXT
    );
    """)
    conn.commit()
    return conn

def processar_e_salvar():
    todos_codigos = []  # manter ordem
    origem_map = {}     # codigo -> (db, tabela) (a primeira ocorrência)

    for db_path in DB_FILES:
        if not os.path.isfile(db_path):
            print(f"[AVISO] arquivo não encontrado: {db_path} — pulando.")
            continue

        try:
            conn = sqlite3.connect(db_path)
        except Exception as e:
            print(f"[ERRO] ao abrir {db_path}: {e}")
            continue

        try:
            tabelas = get_table_names(conn)
            if not tabelas:
                print(f"[INFO] nenhuma tabela em {db_path}")
                continue

            for tabela in tabelas:
                cur = conn.cursor()
                try:
                    cur.execute(f"SELECT * FROM '{tabela}';")
                    rows = cur.fetchall()
                except Exception as e:
                    print(f"[ERRO] lendo tabela {tabela} em {db_path}: {e}")
                    continue

                # pegar a coluna desejada de cada linha, protegendo caso a linha tenha menos colunas
                col_vals = []
                for r in rows:
                    if len(r) > COLUMN_INDEX:
                        col_vals.append(r[COLUMN_INDEX])
                    else:
                        col_vals.append(None)

                codigos = extrair_codigos_de_linhas(col_vals)
                for c in codigos:
                    if c not in origem_map:
                        todos_codigos.append(c)
                        origem_map[c] = (os.path.basename(db_path), tabela)

                print(f"[INFO] Extraídos {len(codigos)} códigos de {db_path} :: {tabela}")
        finally:
            conn.close()

    # remover duplicados mantendo ordem já garantida pelo uso de origem_map
    unique_codigos = todos_codigos  # já construído sem repetir por origem_map check

    # salvar no DB de saída
    out_conn = ensure_output_db(OUTPUT_DB)
    out_cur = out_conn.cursor()
    inserted = 0
    for c in unique_codigos:
        origem_db, origem_tabela = origem_map.get(c, ("", ""))
        try:
            out_cur.execute(f"INSERT OR IGNORE INTO {OUTPUT_TABLE} (codigo, origem_db, origem_tabela) VALUES (?, ?, ?);",
                            (c, origem_db, origem_tabela))
            if out_cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"[ERRO] ao inserir '{c}': {e}")
    out_conn.commit()
    out_conn.close()

    print("\n" + "="*60)
    print(f"[OK] Total de códigos únicos detectados: {len(unique_codigos)}")
    print(f"[OK] Inseridos no DB '{OUTPUT_DB}': {inserted}")
    print(f"[INFO] DB final salvo com a tabela '{OUTPUT_TABLE}'")
    print("="*60)

if __name__ == "__main__":
    processar_e_salvar()

# Caminho do banco que criamos antes
DB_PATH = "codigos_extraidos.db"
OUTPUT_DIR = "barcodes"

# Cria a pasta de saída se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Conecta ao banco
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT codigo FROM codigos;")
rows = cur.fetchall()
conn.close()

# Gera os códigos de barras
print(f"[INFO] Gerando códigos de barras em: {OUTPUT_DIR}")
for i, (codigo,) in enumerate(rows, start=1):
    try:
        filename = os.path.join(OUTPUT_DIR, f"{codigo}")
        barcode_obj = Code128(codigo, writer=ImageWriter())
        barcode_obj.save(filename)
        print(f"[OK] ({i}) Gerado: {filename}")
    except Exception as e:
        print(f"[ERRO] ao gerar {codigo}: {e}")

print("\n[FINALIZADO] Todos os códigos processados ✅")
