import socket
import time
from threading import Thread
import mensagens
import psutil

# Configurações que serão fornecidas pelo usuário
UDP_PORT = None
TCP_PORT = None
DESTINATION_ADDRESS = None
AGENT_ID = None


def initialize_agent():
    """
    Inicializa o agente com entradas do usuário.
    """
    global DESTINATION_ADDRESS, UDP_PORT, TCP_PORT, AGENT_ID
    DESTINATION_ADDRESS = input("Digite o IP do servidor: ").strip()
    UDP_PORT = int(input("Digite a porta UDP do servidor: ").strip())
    TCP_PORT = int(input("Digite a porta TCP do servidor: ").strip())
    AGENT_ID = int(input("Digite o ID do agente: ").strip())


def register_agent():
    sequence = 1
    max_attempts = 3
    attempt = 0

    # Criar mensagem ATIVA em binário
    message = mensagens.create_ativa_message(sequence, AGENT_ID)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)

        while attempt < max_attempts:
            sock.sendto(message, (DESTINATION_ADDRESS, UDP_PORT))
            print(f"[UDP] Mensagem ATIVA enviada (Tentativa {attempt + 1}) para {DESTINATION_ADDRESS}:{UDP_PORT}")

            try:
                response, _ = sock.recvfrom(1024)
                decoded = mensagens.decode_message(response)

                if decoded["type"] == "ACK" and decoded["sequence"] == sequence:
                    print(f"[UDP] ACK recebido para sequência {sequence}. Registro confirmado.")
                    return
            except socket.timeout:
                print(f"[UDP] Timeout aguardando ACK (Tentativa {attempt + 1}).")

            attempt += 1
            time.sleep(3)

        print("[UDP] Número máximo de tentativas atingido. Registro não foi confirmado.")


def udp_receiver():
    """
    Função para receber mensagens do servidor via UDP.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))
    print(f"[UDP] Cliente ouvindo na porta UDP {UDP_PORT} para receber mensagens")

    while True:
        message, address = sock.recvfrom(1024)
        try:
            decoded = mensagens.decode_message(message)
            print(f"[UDP] Mensagem recebida de {address}: {decoded}")
        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {address}: {e}")


def tcp_client():
    """
    Envia uma mensagem para o servidor via TCP.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((DESTINATION_ADDRESS, TCP_PORT))
        message = mensagens.create_ativa_message(1, AGENT_ID)
        s.send(message)
        print(f"[TCP] Mensagem enviada para {DESTINATION_ADDRESS}:{TCP_PORT}")

        response = s.recv(1024)
        decoded = mensagens.decode_message(response)
        print(f"[TCP] Resposta recebida: {decoded}")
    except ConnectionRefusedError:
        print("[TCP] Não foi possível conectar ao servidor.")
    finally:
        s.close()


if __name__ == "__main__":
    # Inicializa o agente com inputs do usuário
    initialize_agent()

    # Realizar registro com tentativas
    register_agent()

    # Iniciar thread para receber mensagens UDP
    udp_receiver_thread = Thread(target=udp_receiver, daemon=True)
    udp_receiver_thread.start()

    # Enviar mensagem TCP como exemplo
    tcp_client_thread = Thread(target=tcp_client)
    tcp_client_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Agente] Encerrado.")
