import socket
import json
from threading import Thread
import mensagens
import parserJSON

AGENTS = {}  # Dicionário para armazenar agentes registrados
TASKS = {}  # Armazenar tarefas do JSON associadas a cada ID


def initialize_server():
    udp_port = int(input("Digite a porta UDP: ").strip())
    tcp_port = int(input("Digite a porta TCP: ").strip())
    json_file = input("Digite o caminho para o arquivo JSON de configuração: ").strip()
    return udp_port, tcp_port, json_file


def load_tasks(json_file):
    """
    Faz o parse do arquivo JSON para carregar as tarefas.
    """
    tasks = parserJSON.carregar_json(json_file)
    if not tasks:
        print("Erro ao carregar o JSON. Verifique o arquivo.")
        exit(1)

    # Mapear tarefas para os agentes
    for task in tasks["tasks"]:
        for device in task["devices"]:
            device_id = device["device_id"]
            TASKS[device_id] = {
                "frequency": task["frequency"],
                "metrics": device.get("device_metrics", {}),
                "link_metrics": device.get("link_metrics", {}),
                "alert_conditions": device.get("alertflow_conditions", {})
            }
    print(f"[Servidor] Tarefas carregadas: {TASKS}")


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
            # Decodifica a mensagem
            decoded = mensagens.decode_message(msg)
            print(f"[UDP] Mensagem recebida de {addr}: {decoded}")

            # Processar registro
            if decoded["type"] == "ATIVA":
                process_registration(sock, addr, decoded)

            elif decoded["type"] == "TASK":
                print(f"[UDP] Tarefa recebida: {decoded}")

        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {addr}: {e}")


def process_registration(sock, addr, decoded):
    """
    Processa o registro do agente e envia as métricas do JSON ao agente registrado.
    """
    agent_id = decoded.get("agent_id")
    sequence = decoded.get("sequence")

    if agent_id not in AGENTS:
        # Armazenar ID e endereço do agente
        AGENTS[agent_id] = {"address": addr, "metrics": TASKS.get(agent_id, {})}
        print(f"[NetTask] Agente registrado: ID {agent_id} de {addr}")
    else:
        print(f"[NetTask] Agente {agent_id} já registrado.")

    # Enviar ACK ao agente
    ack_message = mensagens.create_ack_message(sequence)
    sock.sendto(ack_message, addr)
    print(f"[UDP] ACK enviado para {addr}")

    # Enviar mensagem TASK ao agente com as métricas associadas
    send_task(sock, agent_id)

def send_task(sock, agent_id, sequence, task_data):
    """
    Envia uma mensagem TASK para o agente especificado.
    :param sock: Socket para envio.
    :param agent_id: ID do agente (device_id).
    :param sequence: Número da sequência.
    :param task_data: Dados do JSON para o agente.
    """
    if agent_id not in AGENTS:
        print(f"[NetTask] Agente {agent_id} não registrado.")
        return

    addr = AGENTS[agent_id]
    message = create_task_message(agent_id, sequence, task_data)
    sock.sendto(message, addr)
    print(f"[NetTask] Mensagem TASK enviada para {addr}: {message}")


if __name__ == "__main__":
    # Inicializa o servidor pedindo as portas e JSON ao usuário
    udp_port, tcp_port, json_file = initialize_server()

    # Carregar tarefas do JSON
    load_tasks(json_file)

    # Inicia threads para os servidores UDP e TCP
    udp_server_thread = Thread(target=udp_server, args=(udp_port,), daemon=True)
    udp_server_thread.start()

    print("Servidor UDP rodando. Pressione Ctrl+C para encerrar.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
