import socket
import json
from threading import Thread
import mensagens

AGENTS = {}  # Dicionário para armazenar agentes registrados


def initialize_server():
    """
    Solicita ao usuário as portas UDP e TCP para configurar o servidor.
    """
    udp_port = int(input("Digite a porta UDP: ").strip())
    tcp_port = int(input("Digite a porta TCP: ").strip())
    return udp_port, tcp_port


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
            print(f"[DEBUG] Mensagem recebida bruta de {addr}: {msg}")  # Debug da mensagem recebida

            decoded = mensagens.decode_message(msg)
            print(f"[DEBUG] Mensagem decodificada: {decoded}")  # Debug da mensagem decodificada

            # Processa o registro ou outras ações
            if decoded["type"] == "ATIVA":
                process_registration(sock, addr, decoded)

            elif decoded["type"] == "TASK":
                print(f"[UDP] Tarefa recebida: {decoded}")

        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem: {e}")


def tcp_server(tcp_port):
    """
    Servidor TCP que recebe conexões e processa mensagens.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', tcp_port))
    sock.listen(5)
    print(f"[TCP] Servidor ouvindo na porta TCP {tcp_port}")

    while True:
        try:
            conn, addr = sock.accept()
            print(f"[TCP] Conexão recebida de {addr}")

            msg = conn.recv(1024)
            print(f"[DEBUG] Mensagem recebida (binária) de {addr}: {msg}")

            decoded = mensagens.decode_message(msg)
            print(f"[DEBUG] Mensagem decodificada de {addr}: {decoded}")

            ack_message = mensagens.create_ack_message(decoded["sequence"])
            conn.send(ack_message)
            print("[TCP] ACK enviado.")

        except Exception as e:
            print(f"[TCP] Erro ao processar mensagem de {addr}: {e}")


def process_registration(sock, addr, decoded):
    """
    Processa o registro do agente e envia um ACK de confirmação.
    """
    try:
        agent_id = decoded.get('agent_id')
        sequence = decoded.get('sequence')

        if agent_id is None or sequence is None:
            print(f"[DEBUG] Mensagem ATIVA incompleta: {decoded}")
            return

        # Registrar o agente
        if agent_id not in AGENTS:
            AGENTS[agent_id] = addr
            print(f"[NetTask] Agente registrado: ID {agent_id} de {addr}")
        else:
            print(f"[NetTask] Agente {agent_id} já registrado. Endereço: {AGENTS[agent_id]}")

        # Enviar ACK
        ack_message = mensagens.create_ack_message(sequence)
        print(f"[DEBUG] Enviando ACK para {addr}: {ack_message}")
        sock.sendto(ack_message, addr)

    except Exception as e:
        print(f"[NetTask] Erro ao processar registro: {e}")


if __name__ == "__main__":
    udp_port, tcp_port = initialize_server()

    udp_server_thread = Thread(target=udp_server, args=(udp_port,), daemon=True)
    tcp_server_thread = Thread(target=tcp_server, args=(tcp_port,), daemon=True)

    udp_server_thread.start()
    tcp_server_thread.start()

    print("Servidores UDP e TCP rodando simultaneamente. Pressione Ctrl+C para encerrar.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nServidores encerrados.")
