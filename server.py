import socket
from threading import Thread

# Configurações
UDP_PORT = 33333
TCP_PORT = 44444

# Função para o servidor UDP
def udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))
    print(f"[UDP] Servidor ouvindo na porta UDP {UDP_PORT}")
    while True:
        msg, addr = sock.recvfrom(8192)
        print(f"[UDP] Mensagem recebida de {addr}: {msg.decode()}")
        sock.sendto(b"Mensagem recebida pelo servidor via UDP!", addr)

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

def process_registration(msg, addr):
    """
    Processa o registro do NMS_Agent.
    :param msg: Mensagem recebida.
    :param addr: Endereço do agente.
    """
    decoded = decode_message(msg)
    if decoded["type"] == "ATIVA":
        print(f"[NetTask] Agente registrado: ID {decoded['agent_id']} de {addr}")
        response = create_ack_message(sequence=decoded["sequence"])
        sock.sendto(response, addr)


def send_task(agent_addr, sequence, task_data):
    """
    Envia uma tarefa para o agente.
    :param agent_addr: Endereço do agente.
    :param sequence: Número de sequência.
    :param task_data: Dados da tarefa em JSON.
    :Falta ler o Json
    """
    task_type = 1  # Exemplo: tipo de tarefa (CPU monitoramento) 
    metric = 2  # Exemplo: métrica (RAM uso)
    value = 80  # Exemplo: limite de 80%
    task_msg = create_task_message(sequence, task_type, metric, value)
    sock.sendto(task_msg, agent_addr)
    print(f"[NetTask] Tarefa enviada para {agent_addr}: {task_msg}")
