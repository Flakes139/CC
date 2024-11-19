import socket
import time
from threading import Thread

# Configurações
UDP_PORT = 33333
TCP_PORT = 44444
DESTINATION_ADDRESS = '10.0.0.10'

# Função para envio de mensagem via UDP
def udp_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = ("Hello via UDP!").encode('utf-8') 
    s.sendto(msg, (DESTINATION_ADDRESS, UDP_PORT))
    print(f"[UDP] Mensagem enviada: {msg} para {DESTINATION_ADDRESS} porta {UDP_PORT}")
    s.close()

# Função para recepção de mensagens via UDP
def udp_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))
    print(f"[UDP] Cliente ouvindo na porta UDP {UDP_PORT}")
    while True:
        message, address = sock.recvfrom(1024)
        print(f"[UDP] Mensagem recebida: {message.decode()} de {address}")

# Função para envio de mensagem via TCP
def tcp_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((DESTINATION_ADDRESS, TCP_PORT))
        msg = "Hello via TCP!"
        s.send(msg.encode('utf-8'))
        print(f"[TCP] Mensagem enviada: {msg} para {DESTINATION_ADDRESS} porta {TCP_PORT}")
        response = s.recv(1024).decode('utf-8')
        print(f"[TCP] Resposta recebida do servidor: {response}")
    except ConnectionRefusedError:
        print("[TCP] Não foi possível conectar ao servidor.")
    finally:
        s.close()

# Iniciar envio de mensagens UDP e TCP
if __name__ == "__main__":
    # Enviar mensagem UDP
    udp_client_thread = Thread(target=udp_client)
    udp_receiver_thread = Thread(target=udp_receiver, daemon=True)
    tcp_client_thread = Thread(target=tcp_client)

    udp_client_thread.start()
    udp_receiver_thread.start()
    tcp_client_thread.start()

    # Esperar que os clientes terminem
    udp_client_thread.join()
    tcp_client_thread.join()

    # Manter o programa ativo para recepção UDP
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCliente encerrado.")

def register_agent(agent_id):
    """
    Registra o agente no servidor.
    :param agent_id: ID único do agente.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = create_ativa_message(sequence=1, agent_id=agent_id)
    s.sendto(msg, (DESTINATION_ADDRESS, UDP_PORT))
    print(f"[NetTask] Registro enviado: {msg}")
    response, _ = s.recvfrom(1024)
    print(f"[NetTask] Resposta do servidor: {response}")
    s.close()

def process_received_task(msg):
    """
    Processa uma mensagem de tarefa recebida.
    :param msg: Mensagem recebida.
    """
    decoded = decode_message(msg)
    if decoded["type"] == "TASK":
        print(f"[NetTask] Tarefa recebida: {decoded}")
        # Aqui você pode iniciar a execução das métricas solicitadas
