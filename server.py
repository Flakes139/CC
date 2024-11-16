import socket
from threading import Thread

# Configurações
UDP_PORT = 33333
TCP_PORT = 44444

# Função para o servidor UDP
def udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))
    print(f"[UDP] Servidor ouvindo na porta UDP {UDP_PORT}")
    while True:
        msg, addr = sock.recvfrom(8192)
        print(f"[UDP] Mensagem recebida de {addr}: {msg.decode()}")
        sock.sendto(b"Mensagem recebida pelo servidor via UDP!", addr)

# Função para o servidor TCP
def tcp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', TCP_PORT))
    sock.listen(5)
    print(f"[TCP] Servidor ouvindo na porta TCP {TCP_PORT}")
    while True:
        conn, addr = sock.accept()
        print(f"[TCP] Conexão recebida de {addr}")
        msg = conn.recv(1024).decode('utf-8')
        print(f"[TCP] Mensagem recebida: {msg}")
        conn.send(b"Mensagem recebida pelo servidor via TCP!")
        conn.close()

# Iniciar os servidores em threads separadas
if __name__ == "__main__":
    udp_server_thread = Thread(target=udp_server, daemon=True)
    tcp_server_thread = Thread(target=tcp_server, daemon=True)

    udp_server_thread.start()
    tcp_server_thread.start()

    print("Servidores UDP e TCP rodando simultaneamente. Pressione Ctrl+C para encerrar.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nServidores encerrados.")
