import socket
import time
from threading import Thread

# Configurações
UDP_PORT = 33333
BROADCAST_PORT = 33333
DESTINATION_ADDRESS = '10.0.0.10'

# Cliente UDP básico
def udp_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = ("Hello you there!").encode('utf-8') 
    s.sendto(msg, ('10.0.0.10', UDP_PORT))
    print(f"Mensagem enviada: {msg} para localhost porta {UDP_PORT}")
    s.close()

# Cliente-servidor UDP (envio e recepção contínuos)
def udp_client_server():
    # Criar socket UDP e configurar broadcast e reutilização de endereço
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', BROADCAST_PORT))

    # Função para enviar mensagens periodicamente
    def send_message(msg):
        while True:
            print(f"Enviando mensagem: {msg} para {DESTINATION_ADDRESS} porta {BROADCAST_PORT}")
            sock.sendto(msg, (DESTINATION_ADDRESS, BROADCAST_PORT))
            time.sleep(1)

    # Função para receber mensagens
    def receive_message():
        while True:
            message, address = sock.recvfrom(1024)
            print(f"Mensagem recebida: {message.decode()} de {address}")

    # Criar threads para enviar e receber mensagens
    message = ("HELLO!").encode('utf-8')
    send_thread = Thread(target=send_message, args=(message,))
    receive_thread = Thread(target=receive_message)
    send_thread.start()
    receive_thread.start()

    # Aguardar o término das threads
    send_thread.join()
    receive_thread.join()

# Executar o agente
if __name__ == "__main__":
    print("1. Enviar mensagem UDP básica")
    print("2. Iniciar cliente-servidor UDP")
    choice = input("Escolha a opção (1/2): ").strip()

    if choice == "1":
        udp_client()
    elif choice == "2":
        udp_client_server()
    else:
        print("Opção inválida.")
