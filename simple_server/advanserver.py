import socket


def start_server(host, port):
    # Cria um socket TCP/IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Associa o socket com o host e porta especificados
        server_socket.bind((host, port))
        # Escuta por conexões
        server_socket.listen()

        print(f"Servidor iniciado em {host}:{port}")

        # Aceita conexões e as trata
        while True:
            # Aceita nova conexão
            client_socket, client_address = server_socket.accept()

            print(f"Conexão recebida de {client_address[0]}:{client_address[1]}")

            data = client_socket.recv(1024).decode()
            if data:
                print(data)

            # Fecha o socket do cliente
            client_socket.close()


if __name__ == "__main__":
    HOST = '192.168.15.155'  # Endereço IP padrão para conexões locais
    PORT = 1194        # Porta que o servidor irá escutar

    start_server(HOST, PORT)

