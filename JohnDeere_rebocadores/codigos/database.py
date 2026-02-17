import sqlite3 as sql
import sys
import os


try:
    # Database configuration / Configuração do banco de dados
    file_name = 'john.db'
    exe_path = ""

    # Check if it is an exe or a script / Verifica se é um exe ou script
    if getattr(sys, 'frozen', False):
        exe_path = os.path.dirname(sys.executable)
    elif __file__:
        exe_path = os.path.dirname(__file__)

    config_path = os.path.join(exe_path, file_name)  # Find the path of the database / Acha o caminho do banco de dados

    # SQL Models / Modelos SQL
    insert_data = ''' INSERT INTO dados(tugger_id, date_time, gps_latitude, gps_longitude, gps_altitude, 
    gps_signal_quality, gps_satellite_count, gps_pdop, gps_hdop, gps_vdop, gps_speed, gps_direction,
    tugger_status, current_value, internet_connected, reverse_gear_status, badge) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?); '''

    model_size_sql = ''' SELECT COUNT(tugger_id) FROM dados; '''

    model_get_all_table = ''' SELECT * FROM dados; '''
    model_get_10_table = ''' SELECT * FROM dados ORDER BY id LIMIT 10; '''

    model_delete_all_table = ''' DELETE FROM dados; '''

    model_create_table = ''' CREATE TABLE IF NOT EXISTS dados( id INTEGER PRIMARY KEY AUTOINCREMENT, 
    tugger_id VARCHAR(20), date_time VARCHAR(20),
    gps_latitude VARCHAR(20), gps_longitude VARCHAR(20), gps_altitude VARCHAR(20), 
    gps_signal_quality VARCHAR(20), gps_satellite_count VARCHAR(20), 
    gps_pdop VARCHAR(20), gps_hdop VARCHAR(20), gps_vdop VARCHAR(20),
    gps_speed VARCHAR(20), gps_direction VARCHAR(20),
    tugger_status VARCHAR(4), current_value VARCHAR(20), internet_connected VARCHAR(20),
    reverse_gear_status VARCHAR(4), badge VARCHAR(20)); '''

    # Create or verify the table / Criar ou verificar a tabela
    connection = sql.connect(config_path)
    cur = connection.cursor()  # Create cursor to modify the database / Cria cursor para modificar o banco de dados
    cur.execute(model_create_table)
    cur.close()
    connection.close()

except Exception as a:
    print(f"Error in database configuration: {a}")


# Function to update the database / Função para atualizar o banco de dados
def update_sql(tugger_id, date_time, gps_latitude, gps_longitude, gps_altitude, gps_signal_quality,
               gps_satellite_count, gps_pdop, gps_hdop, gps_vdop, gps_speed, gps_direction,
               tugger_status, current_value, badge, internet_connected, reverse_gear_status):

    try:
        conn = sql.connect(config_path)
        curs = conn.cursor()  # Create cursor to modify the database / Cria cursor para modificar o banco de dados
        curs.execute(insert_data, (
            tugger_id, date_time, gps_latitude, gps_longitude, gps_altitude, gps_signal_quality, gps_satellite_count,
            gps_pdop, gps_hdop, gps_vdop, gps_speed, gps_direction, tugger_status, current_value,
            internet_connected, reverse_gear_status, badge))
        conn.commit()
        curs.close()
        conn.close()
    except Exception as b:
        print(f"Error in database update: {b}")
        pass
    

# Function to get the size of the table / Função para obter o tamanho da tabela
def get_sql_size():
    try:
        conn = sql.connect(config_path)
        curs = conn.cursor()  # Create cursor to modify the database / Cria cursor para modificar o banco de dados

        curs.execute(model_size_sql)
        size = curs.fetchone()

        curs.close()
        conn.close()
        return size[0]
    except Exception as c:
        print(f"Error in fetching database size: {c}")
        return 0


# Function to get the first 10 records / Função para obter os primeiros 10 registros
def get_10_sql():
    try:
        conn = sql.connect(config_path)
        curs = conn.cursor()  # Create cursor to modify the database / Cria cursor para modificar o banco de dados

        curs.execute(model_get_10_table)
        rows = curs.fetchall()
        result = []
        for row in rows:
            d = {}
            for i, col in enumerate(curs.description):
                d[col[0]] = row[i]
            result.append(d)
        # Returns the result as a JSON-like list / Retorna o resultado como uma lista estilo JSON

        curs.close()
        conn.close()
        return result
    except Exception as d:
        print(f"Error in fetching 10 records from the database: {d}")
        return None


# Function to delete X records / Função para deletar X registros
def delete_x_sql(qnt):
    try:
        conn = sql.connect(config_path)
        curs = conn.cursor()  # Create cursor to modify the database / Cria cursor para modificar o banco de dados
        model_delete_x_table = f''' DELETE FROM dados WHERE id IN (SELECT id FROM 
        (SELECT id FROM dados ORDER BY id LIMIT {qnt}) AS subquery); '''
        curs.execute(model_delete_x_table)
        conn.commit()
        curs.close()
        conn.close()

    except Exception as f:
        print(f"Error in deleting items from the database: {f}")
