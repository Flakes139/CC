import socket
import json
import mensagens
from threading import Thread

# Configurações
UDP_PORT = 33333
TCP_PORT = 44444
AGENTS = {}  # Dicionário para armazenar agentes registrados
TASKS = {
    "task_id": "task-202",
    "frequency": 20,
    "metrics": ["cpu_usage", "ram_usage"]  # Exemplo de métricas
}

def udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))
    print(f"[UDP] Servidor ouvindo na porta UDP {UDP_PORT}")

    while True:
        # Recebe mensagem em binário
        msg, addr = sock.recvfrom(8192)
        try:
            # Decodifica a mensagem usando mensagens.decode_message
            decoded = mensagens.decode_message(msg)
            print(f"[UDP] Mensagem recebida de {addr}: {decoded}")

            if decoded["type"] == "ATIVA":
                # Enviar ACK em resposta
                ack_message = mensagens.create_ack_message(decoded["sequence"])
                sock.sendto(ack_message, addr)
                print(f"[UDP] ACK enviado para {addr}")

            elif decoded["type"] == "TASK":
                # Processar mensagens do tipo TASK
                print(f"[UDP] Tarefa recebida: {decoded}")

            # Chama a função process_registration e passa o sock para ela
            process_registration(sock, addr, msg)  # Passando sock como parâmetro

            # Enviar tarefa para o agente
            send_task(sock, addr, decoded["sequence"], TASKS)  # Passando sock como parâmetro

        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {addr}: {e}")

# Função para o servidor TCP
def tcp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', TCP_PORT))
    sock.listen(5)
    print(f"[TCP] Servidor ouvindo na porta TCP {TCP_PORT}")

    while True:
        conn, addr = sock.accept()
        print(f"[TCP] Conexão recebida de {addr}")

        # Receber mensagem
        msg = conn.recv(1024)
        try:
            decoded = mensagens.decode_message(msg)  # Decodifica o binário
            print(f"[TCP] Mensagem recebida: {decoded}")

            # Enviar resposta (binário)
            ack_message = mensagens.create_ack_message(decoded["sequence"])
            conn.send(ack_message)
            print("[TCP] ACK enviado.")
        except Exception as e:
            print(f"[TCP] Erro ao processar mensagem de {addr}: {e}")

        conn.close()

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

def process_registration(sock, msg, addr):
    """
    Processa o registro do NMS_Agent.
    :param msg: Mensagem recebida.
    :param addr: Endereço do agente.
    """
    decoded = mensagens.decode_message(msg)
    if decoded["type"] == "ATIVA":
        agent_id = decoded['agent_id']
        
        if agent_id not in AGENTS:
            AGENTS[agent_id] = addr  # Armazena endereço do agente
            print(f"[NetTask] Agente registrado: ID {agent_id} de {addr}")
        else:
            print(f"[NetTask] Agente {agent_id} já registrado.")

        # Enviar ACK ao agente
        response = mensagens.create_ack_message(sequence=decoded["sequence"])
        sock.sendto(response, addr)


def send_task(sock, agent_id, sequence, task_data):
    """
    Envia uma tarefa para o agente especificado.
    :param sock: Socket para enviar a mensagem.
    :param agent_id: ID do agente para o qual a tarefa será enviada.
    :param sequence: Número de sequência da mensagem.
    :param task_data: Dados da tarefa (exemplo: dict com task_id, frequency, metrics).
    """
    if agent_id not in AGENTS:
        print(f"[NetTask] Agente {agent_id} não encontrado para envio de tarefa.")
        return

    # Recupera o endereço do agente registrado
    agent_addr = AGENTS[agent_id]

    # Cria a mensagem de tarefa usando o módulo mensagens
    task_msg = mensagens.create_task_message(sequence, task_data)
    
    # Envia a mensagem para o agente
    sock.sendto(task_msg, agent_addr)
    print(f"[NetTask] Tarefa enviada para {agent_addr}: {task_msg}")
