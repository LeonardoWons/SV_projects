import pyodbc

# Connection string for RFID database / String de conexão para o banco de dados RFID
dados_conexao_rfid = (
    "Driver={ODBC Driver 17 for SQL Server};"  # SQL Server driver name / Nome do driver do SQL Server
    "Server=cq-logistic-projects-prod-cq-db.jdnet.deere.com,1434;;"  # Database server / Servidor onde está o banco de dados
    "Database=CQ_LOGISTIC_PROJECTS;"  # Database name / Nome do banco de dados
    "UID=ACQ0225;"  # User ID / Nome de usuário
    "PWD=fZhJQYO1t!;"  # Password / Senha
)


# Function to test the connection with the RFID database / Função para testar a conexão com o banco de dados RFID
def test_rfid_connection():
    try:
        # Set connection timeouts / Definir tempos de conexão
        pyodbc.SQL_ATTR_CONNECTION_TIMEOUT = 1
        pyodbc.SQL_ATTR_LOGIN_TIMEOUT = 1
        pyodbc.SQL_LOGIN_TIMEOUT = 1

        # Attempt to connect to the database / Tentar conectar ao banco de dados
        conn = pyodbc.connect(dados_conexao_rfid, timeout=1)
        conn.timeout = 1  # Set additional timeout / Definir tempo limite adicional
        conn.close()  # Close the connection / Fechar a conexão
        return True  # Return True if the connection is successful / Retornar True se a conexão for bem-sucedida

    except pyodbc.Error as e:
        print(f'Connection failed: {e}')  # Connection error message / Mensagem de erro de conexão
        return False  # Return False if the connection fails / Retornar False se a conexão falhar


# Function to collect RFID badges / Função para coletar os crachás RFID
def collect_rfids():

    try:
        # Establish connection / Estabelecer conexão
        conn = pyodbc.connect(dados_conexao_rfid, autocommit=False)
        cursor = conn.cursor()

        # SQL query to select formatted badges / Consulta SQL para selecionar os crachás formatados
        query = ''' SELECT BADGE_FORMATADA FROM Telemetry_Badges; '''
        cursor.execute(query)

        # Fetch all rows returned by the query / Buscar todas as linhas retornadas pela consulta
        rows = cursor.fetchall()
        
        # Extract the badge value from each row (each row is a tuple) /
        # Extrair o valor do crachá de cada linha (cada linha é uma tupla)
        badges = [row[0] for row in rows]

        # Close the connection / Fechar a conexão
        conn.close()

        # Return the list of badges / Retornar a lista de crachás
        return badges

    except Exception as r:
        print(f"Error occurred while collecting RFID badges. {r}")  # Error message / Mensagem de erro
        return "error"  # Return "error" if something goes wrong / Retornar "erro" se algo der errado
