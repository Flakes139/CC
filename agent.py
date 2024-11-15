import socket

# Configurações
SERVER_ADDRESS = "127.0.0.1"
UDP_PORT = 6667
TCP_PORT = 6668

# Função para o cliente UDP
def udp_client():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = b"Hello World via UDP!"
    print(f"Enviando mensagem UDP: {message}")
    udp_socket.sendto(message, (SERVER_ADDRESS, UDP_PORT))
    response, _ = udp_socket.recvfrom(1024)
    print(f"Resposta do servidor UDP: {response.decode()}")
    udp_socket.close()

# Função para o cliente TCP
def tcp_client():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((SERVER_ADDRESS, TCP_PORT))
    message = "Hello World via TCP!"
    print(f"Enviando mensagem TCP: {message}")
    tcp_socket.send(message.encode())
    response = tcp_socket.recv(1024)
    print(f"Resposta do servidor TCP: {response.decode()}")
    tcp_socket.close()

# Executar os clientes
if __name__ == "__main__":
    udp_client()
    tcp_client()