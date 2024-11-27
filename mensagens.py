import struct

# Define os tipos de mensagem
MESSAGE_TYPES = {
    "ATIVA": 0x01,  # Registro
    "ACK": 0x02,    # Confirmação
    "TASK": 0x03,   # Tarefas e métricas
}

# Função para criar uma mensagem ATIVA
def create_ativa_message(sequence, agent_id):
    """
    Cria uma mensagem de registro (ATIVA).
    :param sequence: Número de sequência (1 byte).
    :param agent_id: ID do agente (1 byte).
    :return: Mensagem serializada (3 bytes).
    """
    message_type = MESSAGE_TYPES["ATIVA"]
    return struct.pack("!BBB", message_type, sequence, agent_id)

# Função para criar uma mensagem ACK
def create_ack_message(sequence):
    """
    Cria uma mensagem de confirmação (ACK).
    :param sequence: Número de sequência (1 byte).
    :return: Mensagem serializada (2 bytes).
    """
    message_type = MESSAGE_TYPES["ACK"]
    return struct.pack("!BB", message_type, sequence)

# Função para criar uma mensagem TASK
def create_task_message(agent_id, sequence, task_data):
    """
    Cria uma mensagem TASK personalizada para cada agente com base nas métricas no JSON.
    :param agent_id: ID do agente (device_id).
    :param sequence: Número da sequência da mensagem.
    :param task_data: Dicionário com os dados da tarefa para o agente.
    :return: Mensagem serializada (binária).
    """
    # Tipo da mensagem (TASK)
    msg_type = 0x03  # TASK
    
    # Frequência da tarefa
    frequency = task_data["frequency"]

    # Iniciar a mensagem com tipo e sequência
    message = struct.pack("!BB", msg_type, sequence)

    if agent_id == "1":
        # CPU e RAM métricas
        cpu_active = 1 if task_data["device_metrics"]["cpu_usage"] else 0
        ram_active = 1 if task_data["device_metrics"]["ram_usage"] else 0
        cpu_threshold = task_data["alertflow_conditions"]["cpu_usage"]
        ram_threshold = task_data["alertflow_conditions"]["ram_usage"]

        message += struct.pack("!BBBHH", frequency, cpu_active, ram_active, cpu_threshold, ram_threshold)

    elif agent_id == "2":
        # Latência (Ping)
        ping_active = 1
        ping_dest = socket.inet_aton(task_data["link_metrics"]["latency"]["ping"]["destination"])
        packet_count = task_data["link_metrics"]["latency"]["ping"]["packet_count"]
        latency_threshold = task_data["alertflow_conditions"]["latency"]

        message += struct.pack("!BB4sBH", frequency, ping_active, ping_dest, packet_count, latency_threshold)

    elif agent_id == "3":
        # Bandwidth (iperf)
        bandwidth_active = 1
        role = 1 if task_data["link_metrics"]["bandwidth"]["iperf"]["role"] == "client" else 0
        transport = 1 if task_data["link_metrics"]["bandwidth"]["iperf"]["transport"] == "tcp" else 0
        test_duration = task_data["link_metrics"]["bandwidth"]["iperf"]["test_duration"]
        bandwidth_threshold = task_data["alertflow_conditions"]["bandwidth"]

        message += struct.pack("!BBBBBH", frequency, bandwidth_active, role, transport, test_duration, bandwidth_threshold)

    return message

# Função para decodificar mensagens
def decode_message(data):
    """
    Decodifica uma mensagem recebida.
    :param data: Mensagem em binário.
    :return: Dicionário com os campos da mensagem.
    """
    message_type = data[0]

    if message_type == MESSAGE_TYPES["ATIVA"]:
        _, sequence, agent_id = struct.unpack("!BBB", data)
        return {"type": "ATIVA", "sequence": sequence, "agent_id": agent_id}
    elif message_type == MESSAGE_TYPES["ACK"]:
        _, sequence = struct.unpack("!BB", data)
        return {"type": "ACK", "sequence": sequence}
    elif message_type == MESSAGE_TYPES["TASK"]:
        _, sequence, task_type, metric, value = struct.unpack("!BBBBB", data)
        return {
            "type": "TASK",
            "sequence": sequence,
            "task_type": task_type,
            "metric": metric,
            "value": value,
        }
    else:
        return {"type": "UNKNOWN", "raw_data": data}

# Testes
if __name__ == "__main__":
    # Testando mensagem ATIVA
    ativa_msg = create_ativa_message(1, 42)
    print("Mensagem ATIVA:", ativa_msg, decode_message(ativa_msg))

    # Testando mensagem ACK
    ack_msg = create_ack_message(2)
    print("Mensagem ACK:", ack_msg, decode_message(ack_msg))

    # Testando mensagem TASK
    task_msg = create_task_message(3, 1, 2, 100)
    print("Mensagem TASK:", task_msg, decode_message(task_msg))
