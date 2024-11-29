import socket
import json
from threading import Thread
import mensagens
from parserJSON import carregar_tarefas

AGENTS = {}  # Dicionário para armazenar agentes registrados e seus IPs e portas
TASKS = []  # Lista de tarefas carregadas do JSON


def initialize_server():
    """
    Solicita ao usuário a porta UDP e o caminho do JSON para configurar o servidor.
    """
    udp_port = int(input("Digite a porta UDP: ").strip())
    json_path = input("Digite o caminho para o arquivo JSON de configuração: ").strip()

    # Carregar tarefas do JSON
    global TASKS
    TASKS = carregar_tarefas(json_path)
    print(f"[Servidor] Tarefas carregadas: {TASKS}")

    return udp_port


def udp_server(udp_port):
    """
    Servidor UDP que recebe mensagens de agentes e processa.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', udp_port))
    print(f"[UDP] Servidor ouvindo na porta UDP {udp_port}")

    while True:
        try:
            msg, addr = sock.recvfrom(8192)
            decoded = mensagens.decode_message(msg)
            print(f"[UDP] Mensagem recebida de {addr}: {decoded}")

            if decoded["type"] == "ATIVA":
                process_registration(sock, addr, decoded)
            elif decoded["type"] == "ACK":
                print(f"[NetTask] ACK recebido do agente em {addr}.")
            else:
                print(f"[UDP] Tipo de mensagem desconhecido de {addr}: {decoded}")
        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {addr}: {e}")


def process_registration(sock, addr, decoded):
    """
    Processa o registro do agente, armazena seu IP e porta automaticamente do `addr`,
    e envia um ACK de confirmação. Em seguida, envia as tarefas correspondentes.
    """
    agent_id = decoded.get('agent_id')

    # Armazena o IP e a porta diretamente do endereço recebido
    if agent_id not in AGENTS:
        AGENTS[agent_id] = addr  # `addr` já contém (IP, porta UDP)
        print(f"[NetTask] Agente registrado: ID {agent_id} em {addr}")
    else:
        print(f"[NetTask] Agente {agent_id} já registrado em {AGENTS[agent_id]}")

    # Enviar ACK ao agente
    ack_message = mensagens.create_ack_message(decoded["sequence"])
    sock.sendto(ack_message, addr)
    print(f"[UDP] ACK enviado para {addr}")

    # Enviar tarefa ao agente
    send_task_to_agent(sock, agent_id)


def send_task_to_agent(sock, agent_id):
    """
    Envia as tarefas associadas ao agente com base no JSON.
    """
    # Buscar as informações do agente no JSON
    task = next((t for t in TASKS if str(t["device_id"]) == str(agent_id)), None)

    if not task:
        print(f"[NetTask] Nenhuma tarefa encontrada para o agente ID {agent_id}.")
        return

    # Criar mensagem de tarefa em binário
    try:
        task_message = mensagens.create_task_message(
            sequence=1,
            metrics=task["device_metrics"],
            link_metrics=task["link_metrics"],
            alert_conditions=task["alertflow_conditions"]
        )
        print(f"[DEBUG] Tamanho da mensagem de tarefa: {len(task_message)}")

        # Recuperar IP e porta do agente
        agent_addr = AGENTS[agent_id]
        sock.sendto(task_message, agent_addr)
        print(f"[NetTask] Tarefa enviada para o agente ID {agent_id} em {agent_addr}: {task_message}")
    except KeyError as e:
        print(f"[NetTask] Erro ao criar mensagem de tarefa para o agente ID {agent_id}: {e}")
    except Exception as e:
        print(f"[NetTask] Erro inesperado ao enviar tarefa para o agente ID {agent_id}: {e}")


if __name__ == "__main__":
    udp_port = initialize_server()

    udp_server_thread = Thread(target=udp_server, args=(udp_port,), daemon=True)
    udp_server_thread.start()

    print("Servidor rodando. Pressione Ctrl+C para encerrar.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
