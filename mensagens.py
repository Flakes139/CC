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
def create_task_message(sequence, metrics, link_metrics, alert_conditions):
    """
    Cria uma mensagem de tarefa (TASK) em binário.
    :param sequence: Número de sequência da mensagem (1 byte).
    :param device_id: ID do dispositivo (1 byte).
    :param metrics: Métricas do dispositivo (dicionário).
    :param link_metrics: Métricas de link (dicionário).
    :param alert_conditions: Condições de alerta (dicionário).
    :return: Mensagem serializada em binário.
    """
    message_type = MESSAGE_TYPES["TASK"]

    # Serializar métricas como JSON string
    metrics_json = json.dumps({
        "metrics": metrics,
        "link_metrics": link_metrics,
        "alert_conditions": alert_conditions
    }).encode('utf-8')

    # Construir mensagem binária
    return struct.pack("!BB", message_type, sequence) + metrics_json


def decode_message(data):
    """
    Decodifica uma mensagem recebida.
    """
    message_type = data[0]

    if message_type == MESSAGE_TYPES["ATIVA"]:
        _, sequence, agent_id = struct.unpack("!BBB", data)
        return {"type": "ATIVA", "sequence": sequence, "agent_id": agent_id}
    elif message_type == MESSAGE_TYPES["ACK"]:
        _, sequence = struct.unpack("!BB", data)
        return {"type": "ACK", "sequence": sequence}
    elif message_type == MESSAGE_TYPES["TASK"]:
        sequence = data[1]
        payload = json.loads(data[2:].decode('utf-8'))
        return {"type": "TASK", "sequence": sequence, **payload}
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
