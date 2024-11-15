import socket
import threading

# Configurações
UDP_PORT = 6667
TCP_PORT = 6668
BUFFER_SIZE = 1024

# Função para o servidor UDP
def udp_server():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", UDP_PORT))
    print(f"Servidor UDP ouvindo na porta {UDP_PORT}")
    while True:
        message, address = udp_socket.recvfrom(BUFFER_SIZE)
        print(f"Recebido via UDP de {address}: {message.decode()}")
        udp_socket.sendto(b"Mensagem recebida via UDP!", address)

# Função para o servidor TCP
def tcp_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(("0.0.0.0", TCP_PORT))
    tcp_socket.listen(5)
    print(f"Servidor TCP ouvindo na porta {TCP_PORT}")
    while True:
        conn, address = tcp_socket.accept()
        print(f"Conexão TCP de {address}")
        message = conn.recv(BUFFER_SIZE).decode()
        print(f"Recebido via TCP de {address}: {message}")
        conn.send(b"Mensagem recebida via TCP!")
        conn.close()

# Iniciar os servidores em threads diferentes
if __name__ == "__main__":
    threading.Thread(target=udp_server, daemon=True).start()
    threading.Thread(target=tcp_server, daemon=True).start()
    print("Servidores UDP e TCP iniciados. Pressione Ctrl+C para sair.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nServidores encerrados.")