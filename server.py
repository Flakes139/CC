import socket
import json
from threading import Thread
import mensagens
from parserJSON import carregar_tarefas

AGENTS = {}  # Dicionário para armazenar agentes registrados e seus IPs
TASKS = []  # Lista de tarefas carregadas do JSON


def initialize_server():
    """
    Solicita ao usuário as portas UDP e TCP para configurar o servidor.
    """
    udp_port = int(input("Digite a porta UDP: ").strip())
    tcp_port = int(input("Digite a porta TCP: ").strip())
    json_path = input("Digite o caminho para o arquivo JSON de configuração: ").strip()

    # Carregar tarefas do JSON
    global TASKS
    TASKS = carregar_tarefas(json_path)
    print(f"[Servidor] Tarefas carregadas: {TASKS}")

    return udp_port, tcp_port


def udp_server(udp_port):
    """
    Servidor UDP que recebe mensagens de agentes e processa.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', udp_port))
    print(f"[UDP] Servidor ouvindo na porta UDP {udp_port}")

    while True:
        msg, addr = sock.recvfrom(8192)
        try:
            # Decodifica a mensagem usando mensagens.decode_message
            decoded = mensagens.decode_message(msg)
            print(f"[UDP] Mensagem recebida de {addr}: {decoded}")

            if decoded["type"] == "ATIVA":
                process_registration(sock, addr, decoded)

        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {addr}: {e}")


def process_registration(sock, addr, decoded):
    """
    Processa o registro do agente, armazena seu IP e envia um ACK de confirmação.
    Em seguida, envia as tarefas correspondentes com base no JSON.
    """
    agent_id = decoded.get('agent_id')
    if agent_id not in AGENTS:
        AGENTS[agent_id] = addr  # Armazena endereço do agente
        print(f"[NetTask] Agente registrado: ID {agent_id} de {addr}")
    else:
        print(f"[NetTask] Agente {agent_id} já registrado.")

    # Enviar ACK ao agente
    ack_message = mensagens.create_ack_message(decoded["sequence"])
    sock.sendto(ack_message, addr)
    print(f"[UDP] ACK enviado para {addr}")

    # Enviar tarefa ao agente
    send_task_to_agent(sock, agent_id, addr)


def send_task_to_agent(sock, agent_id, addr):
    """
    Envia as tarefas associadas ao agente com base no JSON.
    """
    # Buscar as informações do agente no JSON
    task = next((t for t in TASKS if str(t["device_id"]) == str(agent_id)), None)

    if not task:
        print(f"[NetTask] Nenhuma tarefa encontrada para o agente ID {agent_id}.")
        return

    # Criar mensagem de tarefa em binário
    task_message = mensagens.create_task_message(
        sequence=1,
        metrics=task["device_metrics"],
        link_metrics=task["link_metrics"],
        alert_conditions=task["alertflow_conditions"]
    )

    # Enviar a mensagem para o agente
    sock.sendto(task_message, addr)
    print(f"[NetTask] Tarefa enviada para o agente ID {agent_id} em {addr}: {task_message}")


if __name__ == "__main__":
    # Inicializa o servidor pedindo as portas ao usuário
    udp_port, tcp_port = initialize_server()

    # Inicia threads para os servidores UDP e TCP
    udp_server_thread = Thread(target=udp_server, args=(udp_port,), daemon=True)
    udp_server_thread.start()

    print("Servidor rodando. Pressione Ctrl+C para encerrar.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
