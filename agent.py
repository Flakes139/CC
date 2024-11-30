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


def send_with_ack(sock, message, destination, max_attempts=3):
    """
    Envia uma mensagem e aguarda o ACK.
    Fecha a socket após falha em todas as tentativas.
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
                return True  # ACK recebido com sucesso
        except socket.timeout:
            print(f"[UDP] Timeout aguardando ACK (Tentativa {attempt + 1}).")
        attempt += 1
        time.sleep(3)

    print("[UDP] Número máximo de tentativas atingido. Fechando socket.")
    sock.close()
    return False  # Falha ao receber o ACK


def register_agent(sock, server_ip, udp_port, agent_id):
    """
    Envia uma mensagem ATIVA ao servidor e aguarda o ACK.
    """
    sequence = 1
    message = mensagens.create_ativa_message(sequence, agent_id)
    print(f"[DEBUG] Mensagem ATIVA criada: {message}")

    return send_with_ack(sock, message, (server_ip, udp_port))


def udp_receiver(sock):
    """
    Recebe mensagens do servidor via UDP e imprime as tarefas.
    """
    print(f"[UDP] Cliente ouvindo na porta UDP {sock.getsockname()[1]}")

    while True:
        try:
            message, address = sock.recvfrom(1024)
            decoded = mensagens.decode_message(message)
            print(f"[UDP] Mensagem decodificada recebida do servidor: {decoded}")

            if decoded["type"] == "TASK":
                # Enviar ACK para o servidor
                ack_message = mensagens.create_ack_message(decoded["sequence"])
                sock.sendto(ack_message, address)
                print(f"[UDP] ACK enviado para o servidor em {address}")
        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem: {e}")


if __name__ == "__main__":
    server_ip, udp_port, agent_id = initialize_agent()

    # Criar uma única socket para todo o ciclo de vida do agente
    agent_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    agent_socket.bind(('', 33333))  # Porta fixa para o agente

    # Registrar o agente
    if register_agent(agent_socket, server_ip, udp_port, agent_id):
        # Iniciar o receptor UDP somente se o registro foi bem-sucedido
        udp_receiver_thread = Thread(target=udp_receiver, args=(agent_socket,), daemon=True)
        udp_receiver_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Agente] Encerrado.")
            agent_socket.close()
