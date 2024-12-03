import socket
import json
from threading import Thread
import mensagens
from parserJSON import carregar_tarefas
import time


AGENTS = {}  # Dicionário para armazenar agentes registrados e seus IPs
TASKS = []  # Lista de tarefas carregadas do JSON


import subprocess

def initialize_server():
    """
    Solicita ao usuário a porta UDP e o caminho do JSON para configurar o servidor e inicia o servidor iperf.
    """
    udp_port = 33333
    json_path = "teste.json"

    # Carregar tarefas do JSON
    global TASKS
    TASKS = carregar_tarefas(json_path)
    print(f"[Servidor] Tarefas carregadas: {TASKS}")

    # Inicializar o servidor iperf
    try:
        subprocess.Popen(
            ["iperf3", "-s", "-p 33333"],  # Inicia o iperf no modo servidor
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("[Servidor] Servidor iperf iniciado com sucesso.")
    except Exception as e:
        print(f"[Erro] Não foi possível iniciar o servidor iperf: {e}")

    return udp_port



def send_with_ack(sock, message, destination, max_attempts=3):
    """
    Envia uma mensagem e aguarda o ACK.
    """
    attempt = 0
    sequence = mensagens.decode_message(message).get("sequence", None)

    sock.settimeout(3)  # Define timeout enquanto aguarda o ACK
    while attempt < max_attempts:
        try:
            sock.sendto(message, destination)
            print(f"[UDP] Mensagem enviada para {destination} (Tentativa {attempt + 1})")

            response, _ = sock.recvfrom(1024)
            decoded = mensagens.decode_message(response)
            print(f"[DEBUG] Resposta decodificada: {decoded}")

            if decoded["type"] == "ACK" and decoded["sequence"] == sequence:
                print("[UDP] ACK recebido. Comunicação confirmada.")
                return True
        except socket.timeout:
            print(f"[UDP] Timeout aguardando ACK (Tentativa {attempt + 1}).")
        attempt += 1
        time.sleep(3)

    print("[UDP] Número máximo de tentativas atingido.")
    return False

def process_report(sock, addr, decoded):
    """
    Processa mensagens do tipo REPORT:
    - Dá print no conteúdo recebido.
    - Envia um ACK com até 3 tentativas.
    """
    try:
        # Print da mensagem recebida
        print(f"[NetTask] Relatório recebido de {addr}:")
        print(json.dumps(decoded, indent=2))

        # Obtém o número de sequência da mensagem
        sequence = decoded.get("sequence")
        if sequence is None:
            print(f"[NetTask] Mensagem REPORT sem sequência: {decoded}")
            return

        # Criação do ACK
        ack_message = mensagens.create_ack_message(sequence)
        
        # Enviar ACK com até 3 tentativas
        success = send_with_ack(sock, ack_message, addr)
        if success:
            print(f"[NetTask] ACK confirmado para {addr}.")
        else:
            print(f"[NetTask] Falha ao confirmar ACK para {addr} após 3 tentativas.")

    except Exception as e:
        print(f"[NetTask] Erro ao processar relatório de {addr}: {e}")

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
            elif decoded["type"] == "REPORT":
                process_report(sock, addr, decoded)
            else:
                print(f"[UDP] Tipo de mensagem desconhecido de {addr}: {decoded}")
        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {addr}: {e}")


def process_registration(sock, addr, decoded):
    """
    Processa o registro do agente, armazena seu IP e porta, e envia um ACK.
    """
    try:
        agent_id = decoded.get("agent_id")
        sequence = decoded.get("sequence")

        if agent_id is None or sequence is None:
            print(f"[NetTask] Mensagem de registro incompleta de {addr}: {decoded}")
            return

        if agent_id not in AGENTS:
            AGENTS[agent_id] = addr
            print(f"[NetTask] Agente registrado: ID {agent_id} em {addr}")
        else:
            print(f"[NetTask] Agente {agent_id} já registrado em {AGENTS[agent_id]}")

        ack_message = mensagens.create_ack_message(sequence)
        sock.sendto(ack_message, addr)
        print(f"[UDP] ACK enviado para {addr}")

        send_task_to_agent(sock, agent_id)

    except Exception as e:
        print(f"[UDP] Erro ao processar registro de {addr}: {e}")


def send_task_to_agent(sock, agent_id):
    """
    Envia as tarefas associadas ao agente com base no JSON.
    """
    task = next((t for t in TASKS if str(t["device_id"]) == str(agent_id)), None)

    if not task:
        print(f"[NetTask] Nenhuma tarefa encontrada para o agente ID {agent_id}.")
        return

    try:
        task_message = mensagens.create_task_message(
            sequence=1,
            metrics=task["device_metrics"],
            link_metrics=task["link_metrics"],
            alert_conditions=task["alertflow_conditions"]
        )
        print(f"[DEBUG] Tamanho da mensagem de tarefa: {len(task_message)}")

        agent_addr = AGENTS[agent_id]
        send_with_ack(sock, task_message, agent_addr)
    except Exception as e:
        print(f"[NetTask] Erro ao enviar tarefa para o agente {agent_id}: {e}")


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