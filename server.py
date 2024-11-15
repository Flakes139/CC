from socket import socket, AF_INET, SOCK_DGRAM 

# Configurações do servidor UDP
UDP_PORT = 6667

# Criação do socket UDP
sock = socket(AF_INET, SOCK_DGRAM) 
sock.bind(('localhost', UDP_PORT))

print(f"Servidor ouvindo na porta UDP {UDP_PORT} (forever! Use Ctrl-C to parar)")
try:
    while True:
        msg, addr = sock.recvfrom(8192) 
        print(f"Mensagem recebida de {addr}: {msg.decode()}")
except KeyboardInterrupt:
    print("\nServidor UDP encerrado.")
