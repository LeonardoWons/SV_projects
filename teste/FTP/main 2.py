from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os

# Configurações do usuário
FTP_USER = "camera"
FTP_PASSWORD = "1234"
FTP_DIR = os.path.abspath("ftp_dir")  # Pasta onde as imagens serão salvas
FTP_PORT = 2121

# Cria a pasta se não existir
os.makedirs(FTP_DIR, exist_ok=True)

# Autorizações de acesso
authorizer = DummyAuthorizer()
authorizer.add_user(FTP_USER, FTP_PASSWORD, FTP_DIR, perm="elradfmwMT")  # permissões completas

# Manipulador
handler = FTPHandler
handler.authorizer = authorizer

# Iniciar o servidor
server = FTPServer(("0.0.0.0", FTP_PORT), handler)
print(f"Servidor FTP rodando em porta {FTP_PORT}, pasta: {FTP_DIR}")
server.serve_forever()
