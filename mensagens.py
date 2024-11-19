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
def create_task_message(sequence, task_type, metric, value):
    """
    Cria uma mensagem de tarefa (TASK).
    :param sequence: Número de sequência (1 byte).
    :param task_type: Tipo da tarefa (1 byte).
    :param metric: Métrica a ser monitorada (1 byte).
    :param value: Valor associado à métrica (1 byte).
    :return: Mensagem serializada (5 bytes).
    """
    message_type = MESSAGE_TYPES["TASK"]
    return struct.pack("!BBBBB", message_type, sequence, task_type, metric, value)

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
