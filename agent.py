import socket
import time
from threading import Thread
import mensagens


def initialize_agent():
    """
    Solicita ao usuário o IP do servidor, porta UDP e ID do agente.
    """
    server_ip = input("Digite o IP do servidor: ").strip()
    udp_port = int(input("Digite a porta UDP do servidor: ").strip())
    agent_id = int(input("Digite o ID do agente: ").strip())
    return server_ip, udp_port, agent_id


def register_agent(server_ip, udp_port, agent_id):
    """
    Envia uma mensagem ATIVA ao servidor e aguarda o ACK.
    """
    sequence = 1
    max_attempts = 3
    attempt = 0

    message = mensagens.create_ativa_message(sequence, agent_id)
    print(f"[DEBUG] Mensagem ATIVA criada: {message}")  # Debug da mensagem ATIVA

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)

        while attempt < max_attempts:
            try:
                sock.sendto(message, (server_ip, udp_port))
                print(f"[UDP] Mensagem ATIVA enviada (Tentativa {attempt + 1}) para {server_ip}:{udp_port}")

                response, _ = sock.recvfrom(1024)
                print(f"[DEBUG] Resposta recebida (bruta): {response}")  # Debug da resposta bruta

                decoded = mensagens.decode_message(response)
                print(f"[DEBUG] Resposta decodificada: {decoded}")  # Debug da resposta decodificada

                if decoded["type"] == "ACK" and decoded["sequence"] == sequence:
                    print(f"[UDP] ACK recebido para sequência {sequence}. Registro confirmado.")
                    return
            except socket.timeout:
                print(f"[UDP] Timeout aguardando ACK (Tentativa {attempt + 1}).")
            except Exception as e:
                print(f"[UDP] Erro ao enviar mensagem ATIVA: {e}")

            attempt += 1
            time.sleep(3)

        print("[UDP] Número máximo de tentativas atingido. Registro não foi confirmado.")


def udp_receiver(udp_port, server_ip):
    """
    Recebe mensagens do servidor via UDP e envia um ACK de confirmação.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', udp_port))
    print(f"[UDP] Cliente ouvindo na porta UDP {udp_port}")

    while True:
        try:
            message, address = sock.recvfrom(1024)
            print(f"[DEBUG] Mensagem recebida (bruta) de {address}: {message}")

            decoded = mensagens.decode_message(message)
            print(f"[DEBUG] Mensagem decodificada: {decoded}")

            if decoded["type"] == "TASK":
                print(f"[UDP] Tarefa recebida: {decoded}")

                # Criar mensagem de ACK para a tarefa
                ack_message = mensagens.create_ack_message(decoded["sequence"])
                sock.sendto(ack_message, (server_ip, udp_port))
                print(f"[UDP] ACK enviado para o servidor em {server_ip}:{udp_port}")
        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem de {address}: {e}")


if __name__ == "__main__":
    # Solicita os dados de inicialização
    server_ip, udp_port, agent_id = initialize_agent()

    # Realiza registro do agente
    register_agent(server_ip, udp_port, agent_id)

    # Inicia o receptor UDP em uma thread
    udp_receiver_thread = Thread(target=udp_receiver, args=(udp_port, server_ip), daemon=True)
    udp_receiver_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Agente] Encerrado.")
