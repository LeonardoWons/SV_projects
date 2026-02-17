import pyodbc

# Database connection string / String de conexão com o banco de dados

# TABLE = Telemetry
dados_conexao_sql = (
    "Driver={ODBC Driver 17 for SQL Server};"  # SQL Server driver name / Nome do driver do SQL Server
    "Server=cq-logistic-projects-prod-cq-db.jdnet.deere.com,1434;;"  # Database server / Servidor onde está o banco de dados
    "Database=CQ_LOGISTIC_PROJECTS;"  # Database name / Nome do banco de dados
    "UID=ACQ0225;"  # User ID / Nome de usuário
    "PWD=fZhJQYO1t!;"  # Password / Senha
)


# Function to test SQL connection / Função para testar conexão com o SQL
def test_sql_connection():
    try:
        # Set connection timeouts / Definir tempos de conexão
        pyodbc.SQL_ATTR_CONNECTION_TIMEOUT = 1
        pyodbc.SQL_LOGIN_TIMEOUT = 1

        # Attempt to connect to the database / Tentar conectar ao banco de dados
        conn = pyodbc.connect(dados_conexao_sql, timeout=1)
        conn.close()  # Close connection / Fechar conexão
        return True

    except pyodbc.Error as e:
        print(f'Connection failed: {e}')  # Connection error message / Mensagem de erro de conexão
        return False


# Function to send data to SQL / Função para enviar dados para o SQL
def send_to_sql_john(data):
    sent_count = 0  # Counter for sent records / Contador para registros enviados

    try:
        # Set connection timeouts / Definir tempos de conexão
        pyodbc.SQL_ATTR_CONNECTION_TIMEOUT = 1
        pyodbc.SQL_LOGIN_TIMEOUT = 1

        conn_s = pyodbc.connect(dados_conexao_sql,
                              autocommit=False, timeout=1)  # Connect with manual commit / Conectar com commit manual

        cursor = conn_s.cursor()
        
        # SQL insert query / Consulta SQL para inserção
        insert_query = '''INSERT INTO Telemetry(tugger_id, date_time, gps_latitude, gps_longitude, gps_altitude, 
                gps_signal_quality, gps_satellite_count, gps_pdop, gps_hdop, gps_vdop, gps_speed, gps_direction,
                tugger_status, current_value, internet_connected, reverse_gear_status, badge, pc_name) 
                VALUES(
                (SELECT id FROM Telemetry_ComputerNames WHERE computer_name = ?),?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        # Insert data row by row / Inserir dados linha por linha
        for row in data:
            cursor.execute(insert_query, (row['tugger_id'], row['date_time'],
                                          row['gps_latitude'], row['gps_longitude'], row['gps_altitude'],
                                          row['gps_signal_quality'], row['gps_satellite_count'],
                                          row['gps_pdop'], row['gps_hdop'], row['gps_vdop'],
                                          row['gps_speed'], row['gps_direction'],
                                          row['tugger_status'], row['current_value'], row['internet_connected'],
                                          row['reverse_gear_status'], row['badge'], row['tugger_id']))
            
            cursor.commit()  # Commit after each insertion / Fazer commit após cada inserção
            sent_count += 1  # Increment the count of sent records / Incrementar o contador de registros enviados

        conn_s.close()  # Close the connection / Fechar a conexão

        return sent_count  # Return the number of records sent / Retornar o número de registros enviados

    except pyodbc.Error as a:
        print(f"Error occurred during SQL insertion. {a}")  # Error message / Mensagem de erro
        return sent_count  # Return the number of successfully sent records /
        # Retornar o número de registros enviados com sucesso
