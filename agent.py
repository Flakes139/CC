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
    """
    Envia uma mensagem ATIVA ao servidor e aguarda o ACK, com até 3 tentativas.
    """
    sequence = 1  # Número de sequência inicial
    max_attempts = 3  # Número máximo de tentativas
    attempt = 0  # Contador de tentativas

    # Criar mensagem ATIVA
    message = mensagens.create_ativa_message(sequence, AGENT_ID)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)  # Tempo limite de 3 segundos para aguardar o ACK

        while attempt < max_attempts:
            # Enviar mensagem ATIVA
            sock.sendto(message, (DESTINATION_ADDRESS, UDP_PORT))
            print(f"[UDP] Mensagem ATIVA enviada (Tentativa {attempt + 1}) para {DESTINATION_ADDRESS}:{UDP_PORT}")

            try:
                # Aguardar resposta (ACK)
                response, _ = sock.recvfrom(1024)
                decoded = mensagens.decode_message(response)

                # Verificar se o ACK foi recebido
                if decoded["type"] == "ACK" and decoded["sequence"] == sequence:
                    print(f"[UDP] ACK recebido para sequência {sequence}. Registro confirmado.")
                    return  # Encerra a função ao receber o ACK
            except socket.timeout:
                # Caso não receba resposta dentro do tempo limite
                print(f"[UDP] Timeout aguardando ACK (Tentativa {attempt + 1}).")

            # Incrementar tentativa
            attempt += 1
            time.sleep(3)  # Aguardar 3 segundos antes da próxima tentativa

        # Se todas as tentativas falharem
        print("[UDP] Número máximo de tentativas atingido. Registro não foi confirmado.")

def process_received_task(msg):
    """
    Processa uma mensagem de tarefa recebida.
    :param msg: Mensagem recebida.
    """
    decoded = mensagens.decode_message(msg)
    if decoded["type"] == "TASK":
        print(f"[NetTask] Tarefa recebida: {decoded}")
        # Aqui você pode iniciar a execução das métricas solicitadas



def udp_receiver():
    """
    Função para receber tarefas do servidor via UDP.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))
    print(f"[UDP] Cliente ouvindo na porta UDP {UDP_PORT} para receber tarefas")

    while True:
        message, address = sock.recvfrom(1024)
        try:
            data = json.loads(message.decode())

            if data["message_type"] == "register_confirm":
                print(f"[UDP] Registro confirmado pelo servidor para o agente {AGENT_ID}.")

            elif data["message_type"] == "task_request":
                print(f"[UDP] Tarefa recebida: {data['task']}")
                task_id = data['task']['task_id']

                # Enviar confirmação da tarefa
                confirm_task_message = {
                    "message_type": "task_confirm",
                    "task_id": task_id,
                    "agent_id": AGENT_ID
                }
                sock.sendto(json.dumps(confirm_task_message).encode('utf-8'), address)
                print(f"[UDP] Confirmação de tarefa enviada para o servidor: {confirm_task_message}")

                # Iniciar coleta de métricas
                Thread(target=collect_and_send_metrics, args=(data['task'],)).start()
        except json.JSONDecodeError:
            print(f"[UDP] Mensagem inválida recebida de {address}: {message}")


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
    """
    Envia uma mensagem para o servidor via TCP.
    """
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
