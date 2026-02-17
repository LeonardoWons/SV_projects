import sqlite3 as sql
import sys
import os

# Database configuration / Configuração do banco de dados
file_name = 'rfid.db'
exe_path = ""

# Check if it is an exe or script / Verifica se é um exe ou script
if getattr(sys, 'frozen', False):
    exe_path = os.path.dirname(sys.executable)
elif __file__:
    exe_path = os.path.dirname(__file__)

config_path = os.path.join(exe_path, file_name)  # Find the path to the database / Acha o caminho do banco de dados

# SQL Models / Modelos SQL
model_create_table = ''' 
CREATE TABLE IF NOT EXISTS rfid(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    badge VARCHAR(20)
); '''

model_insert_data = ''' INSERT INTO rfid(badge) VALUES(?); '''

model_get_all_table_filter_by_badge = ''' SELECT * FROM rfid WHERE badge = ?; '''

model_delete_all_table = ''' DELETE FROM rfid; '''

# Create table if it doesn't exist / Criação da tabela se não existir
connection = sql.connect(config_path)
cur = connection.cursor()  # Create cursor to modify the database|Cria cursor para fazer modificações no banco de dados
cur.execute(model_create_table)
cur.close()
connection.close()


# Function to insert data into the table / Função para inserir dados na tabela
def insert_data(badges):
    """
    Receives a list of all badges, deletes ALL rows from the table, and adds new badges from the list.
    Recebe uma lista de todas as badges, exclui TODA a tabela e adiciona as novas badges da lista.
    """
    connectionn = sql.connect(config_path)
    curr = connectionn.cursor()

    try:
        # Delete all records from the table / Excluir todos os registros da tabela
        curr.execute(model_delete_all_table)

        # Insert new records / Inserir novos registros
        for badge in badges:
            curr.execute(model_insert_data, (badge,))

        # Commit the changes / Commit das alterações
        connectionn.commit()

    except sql.Error as e:
        print(f"Error inserting data: {e}")  # Error message / Mensagem de erro
        connectionn.rollback()  # Rollback if there's an error / Desfazer alterações se houver erro

    finally:
        curr.close()
        connectionn.close()


# Function to search for a specific badge in the table / Função para procurar um crachá específico na tabela
def search_badge(badge):
    connectionnn = sql.connect(config_path)
    cursor = connectionnn.cursor()

    try:
        cursor.execute(model_get_all_table_filter_by_badge, (badge,))
        result = cursor.fetchone()  # Fetch a single result / Traz um único resultado

        if result:
            return True
        else:
            return False

    except sql.Error as e:
        print(f"Error searching badge: {e}")  # Error message / Mensagem de erro
        return False

    finally:
        cursor.close()
        connectionnn.close()
