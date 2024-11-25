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
        msg, addr = sock.recvfrom(8192)
        try:
            # Decodifica a mensagem usando mensagens.decode_message
            decoded = mensagens.decode_message(msg)
            print(f"[UDP] Mensagem recebida de {addr}: {decoded}")

            # Processa o registro ou outras ações, incluindo o envio de ACK
            if decoded["type"] == "ATIVA":
                process_registration(sock, addr, msg)

            elif decoded["type"] == "TASK":
                # Processar mensagens do tipo TASK
                print(f"[UDP] Tarefa recebida: {decoded}")
                # Aqui você pode processar tarefas ou iniciar threads de coleta de métricas

        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {addr}: {e}")


def tcp_server(tcp_port):
    """
    Servidor TCP que recebe conexões e processa mensagens.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', tcp_port))
    sock.listen(5)
    print(f"[TCP] Servidor ouvindo na porta TCP {tcp_port}")

    while True:
        conn, addr = sock.accept()
        print(f"[TCP] Conexão recebida de {addr}")

        # Receber mensagem
        msg = conn.recv(1024)
        try:
            decoded = mensagens.decode_message(msg)  # Decodifica o binário
            print(f"[TCP] Mensagem recebida: {decoded}")

            # Enviar resposta (ACK em binário)
            ack_message = mensagens.create_ack_message(decoded["sequence"])
            conn.send(ack_message)
            print("[TCP] ACK enviado.")
        except Exception as e:
            print(f"[TCP] Erro ao processar mensagem de {addr}: {e}")

        conn.close()


def process_registration(sock, addr, msg):
    """
    Processa o registro do agente e envia um ACK de confirmação.
    """
    decoded = mensagens.decode_message(msg)
    agent_id = decoded.get('agent_id')
    if agent_id not in AGENTS:
        AGENTS[agent_id] = addr
        print(f"[NetTask] Agente registrado: ID {agent_id} de {addr}")
    else:
        print(f"[NetTask] Agente {agent_id} já registrado.")

    ack_message = mensagens.create_ack_message(decoded["sequence"])
    sock.sendto(ack_message, addr)
    print(f"[UDP] ACK enviado para {addr}")


if __name__ == "__main__":
    # Inicializa o servidor pedindo as portas ao usuário
    udp_port, tcp_port = initialize_server()

    # Inicia threads para os servidores UDP e TCP
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
