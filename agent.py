import socket
import time
from threading import Thread
import mensagens


def initialize_agent():
    """
    Solicita ao usuário o IP do servidor, portas UDP/TCP e ID do agente.
    """
    server_ip = input("Digite o IP do servidor: ").strip()
    udp_port = int(input("Digite a porta UDP do servidor: ").strip())
    agent_port = int(input("Digite a porta UDP do agente: ").strip())
    agent_id = int(input("Digite o ID do agente: ").strip())
    return server_ip, udp_port, agent_port, agent_id


def register_agent(server_ip, udp_port, agent_id):
    """
    Envia uma mensagem ATIVA ao servidor e aguarda o ACK.
    """
    sequence = 1
    max_attempts = 3
    attempt = 0

    message = mensagens.create_ativa_message(sequence, agent_id)
    print(f"[DEBUG] Mensagem ATIVA criada: {message}")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)

        while attempt < max_attempts:
            try:
                sock.sendto(message, (server_ip, udp_port))
                print(f"[UDP] Mensagem ATIVA enviada (Tentativa {attempt + 1}) para {server_ip}:{udp_port}")

                response, _ = sock.recvfrom(1024)
                decoded = mensagens.decode_message(response)
                print(f"[DEBUG] Resposta decodificada: {decoded}")

                if decoded["type"] == "ACK" and decoded["sequence"] == sequence:
                    print(f"[UDP] ACK recebido para sequência {sequence}. Registro confirmado.")
                    return
            except socket.timeout:
                print(f"[UDP] Timeout aguardando ACK (Tentativa {attempt + 1}).")
            attempt += 1
            time.sleep(3)

        print("[UDP] Número máximo de tentativas atingido. Registro não foi confirmado.")


def udp_receiver(agent_port):
    """
    Recebe mensagens do servidor via UDP e imprime as tarefas.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', agent_port))
    print(f"[UDP] Cliente ouvindo na porta UDP {agent_port}")

    while True:
        try:
            message, address = sock.recvfrom(1024)
            decoded = mensagens.decode_message(message)
            print(f"[UDP] Mensagem decodificada recebida do servidor: {decoded}")

            if decoded["type"] == "TASK":
                ack_message = mensagens.create_ack_message(decoded["sequence"])
                sock.sendto(ack_message, address)
                print(f"[UDP] ACK enviado para o servidor em {address}")
        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {address}: {e}")


if __name__ == "__main__":
    server_ip, udp_port, agent_port, agent_id = initialize_agent()

    register_agent(server_ip, udp_port, agent_id)

    udp_receiver_thread = Thread(target=udp_receiver, args=(agent_port,), daemon=True)
    udp_receiver_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Agente] Encerrado.")
