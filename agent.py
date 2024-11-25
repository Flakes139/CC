import socket
import json
import time
from threading import Thread
import psutil
import mensagens

# Configurações
UDP_PORT = 33333
TCP_PORT = 44444
DESTINATION_ADDRESS = '10.0.0.10'
AGENT_ID = 42  # ID do agente
REGISTER_INTERVAL = 10  # Intervalo para reenvio do registro, se necessário


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
                response, _ = sock.recvfrom(1024)  # Receber resposta em binário
                decoded = mensagens.decode_message(response)  # Decodificar

                if decoded["type"] == "ACK" and decoded["sequence"] == sequence:
                    print(f"[UDP] ACK recebido para sequência {sequence}. Registro confirmado.")
                    return
            except socket.timeout:
                print(f"[UDP] Timeout aguardando ACK (Tentativa {attempt + 1}).")

            attempt += 1
            time.sleep(3)

        print("[UDP] Número máximo de tentativas atingido. Registro não foi confirmado.")

def process_received_task(msg):
    """
    Processa uma mensagem de tarefa recebida.
    :param msg: Mensagem recebida.
    """
    decoded = mensagens.decode_message(msg)
    if decoded["type"] == "TASK":
        print(f"[NetTask] Tarefa recebida: {decoded}")
        collect_and_send_metrics(decoded) # iniciar coleta de métricas
        
def udp_receiver():
    """
    Função para receber mensagens do servidor via UDP.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))
    print(f"[UDP] Cliente ouvindo na porta UDP {UDP_PORT} para receber mensagens")

    while True:
        # Recebe mensagem em binário
        message, address = sock.recvfrom(1024)
        try:
            decoded = mensagens.decode_message(message)
            print(f"[UDP] Mensagem recebida de {address}: {decoded}")

            if decoded["type"] == "ACK":
                print(f"[UDP] ACK recebido para sequência {decoded['sequence']}.")

        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {address}: {e}")

def collect_and_send_metrics(task):
    """
    Coleta métricas do sistema e envia ao servidor periodicamente.
    """
    frequency = task.get("frequency", 20)
    while True:
        metrics = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "ram_usage": psutil.virtual_memory().percent
        }
        metrics_message = {
            "message_type": "metrics_data",
            "agent_id": AGENT_ID,
            "task_id": task["task_id"],
            "metrics": metrics
        }
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(json.dumps(metrics_message).encode('utf-8'), (DESTINATION_ADDRESS, UDP_PORT))
            print(f"[UDP] Métricas enviadas: {metrics_message}")
        time.sleep(frequency)


def tcp_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((DESTINATION_ADDRESS, TCP_PORT))
        
        # Criar mensagem em binário
        message = mensagens.create_ativa_message(1, AGENT_ID)
        s.send(message)
        print(f"[TCP] Mensagem enviada para {DESTINATION_ADDRESS} porta {TCP_PORT}")

        # Receber resposta
        response = s.recv(1024)
        decoded = mensagens.decode_message(response)
        print(f"[TCP] Resposta recebida: {decoded}")
    except ConnectionRefusedError:
        print("[TCP] Não foi possível conectar ao servidor.")
    finally:
        s.close()


if __name__ == "__main__":
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
