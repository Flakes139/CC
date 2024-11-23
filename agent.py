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
AGENT_ID = "agent-001"
REGISTER_INTERVAL = 10

# Função para registro do agente no servidor via UDP
def register_agent():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        registration_message = {
            "message_type": "register_request",
            "agent_id": AGENT_ID
        }
        s.sendto(json.dumps(registration_message).encode('utf-8'), (DESTINATION_ADDRESS, UDP_PORT))
        print(f"[UDP] Pedido de registro enviado: {registration_message}")

# Função para envio de mensagem via UDP
def udp_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = ("Hello via UDP!").encode('utf-8') 
    s.sendto(msg, (DESTINATION_ADDRESS, UDP_PORT))
    print(f"[UDP] Mensagem enviada: {msg} para {DESTINATION_ADDRESS} porta {UDP_PORT}")
    s.close()

# Função para recepção e confirmação de tarefas via UDP
def udp_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))
    print(f"[UDP] Cliente ouvindo na porta UDP {UDP_PORT} para receber tarefas")

    while True:
        message, address = sock.recvfrom(1024)
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

# Função para coleta e envio periódico de métricas
def collect_and_send_metrics(task):
    frequency = task.get("frequency", 20)
    while True:
        # Coletando métricas reais do sistema
        metrics = {
            "cpu_usage": psutil.cpu_percent(interval=1),  # Percentual de uso de CPU
            "ram_usage": psutil.virtual_memory().percent  # Percentual de uso de RAM
        }
        metrics_message = {
            "message_type": "metrics_data",
            "agent_id": AGENT_ID,
            "task_id": task["task_id"],
            "metrics": metrics
        }

        # Envio das métricas ao servidor
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(json.dumps(metrics_message).encode('utf-8'), (DESTINATION_ADDRESS, UDP_PORT))
            print(f"[UDP] Métricas enviadas: {metrics_message}")

        # Aguardar o próximo envio
        time.sleep(frequency)

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

# Inicializar agente com registro e threads de comunicação
if __name__ == "__main__":
    # Thread para envio do pedido de registro
    register_agent_thread = Thread(target=register_agent)
    # Thread para receber tarefas e confirmar registro
    udp_receiver_thread = Thread(target=udp_receiver, daemon=True)
    
    register_agent_thread.start()
    udp_receiver_thread.start()

    # Manter o programa ativo para recepção e envio de métricas
    try:
        while True:
            time.sleep(REGISTER_INTERVAL)
            # Reenvio do pedido de registro se o agente ainda não estiver registrado
            if not register_agent_thread.is_alive():
                register_agent_thread = Thread(target=register_agent)
                register_agent_thread.start()
    except KeyboardInterrupt:
        print("\nCliente encerrado.")

def register_agent(agent_id):
    """
    Registra o agente no servidor.
    :param agent_id: ID único do agente.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = mensagens.create_ativa_message(sequence=1, agent_id=agent_id)
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
    decoded = mensagens.decode_message(msg)
    if decoded["type"] == "TASK":
        print(f"[NetTask] Tarefa recebida: {decoded}")
        # Aqui você pode iniciar a execução das métricas solicitadas

        
