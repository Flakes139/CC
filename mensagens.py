import struct

# Define os tipos de mensagem
MESSAGE_TYPES = {
    "ATIVA": 0b000,  # Registro
    "ACK": 0b001,    # Confirmação
    "TASK": 0b010,   # Tarefas e métricas
}

# Função para criar uma mensagem ATIVA
def create_ativa_message(sequence, agent_id):
    """
    Cria uma mensagem de registro (ATIVA).
    :param sequence: Número de sequência (0-31).
    :param agent_id: ID do agente (1 byte).
    :return: Mensagem serializada.
    """
    if not (0 <= sequence <= 31):
        raise ValueError("A sequência deve estar entre 0 e 31.")
    message_type = MESSAGE_TYPES["ATIVA"] << 5  # Tipo ocupa os 3 bits mais significativos
    return struct.pack("!BB", message_type | sequence, agent_id)

# Função para criar uma mensagem ACK
def create_ack_message(sequence):
    """
    Cria uma mensagem de confirmação (ACK).
    :param sequence: Número de sequência (0-31).
    :return: Mensagem serializada.
    """
    if not (0 <= sequence <= 31):
        raise ValueError("A sequência deve estar entre 0 e 31.")
    message_type = MESSAGE_TYPES["ACK"] << 5
    return struct.pack("!B", message_type | sequence)

# Função para criar uma mensagem TASK
def create_task_message(sequence, task_type, metric, value):
    """
    Cria uma mensagem de tarefa (TASK).
    :param sequence: Número de sequência (0-31).
    :param task_type: Tipo da tarefa (1 byte).
    :param metric: Métrica (1 byte).
    :param value: Valor da métrica (1 byte).
    :return: Mensagem serializada.
    """
    if not (0 <= sequence <= 31):
        raise ValueError("A sequência deve estar entre 0 e 31.")
    message_type = MESSAGE_TYPES["TASK"] << 5
    return struct.pack("!BBBB", message_type | sequence, task_type, metric, value)

# Função para decodificar mensagens
def decode_message(data):
    """
    Decodifica uma mensagem recebida.
    :param data: Mensagem em binário.
    :return: Dicionário com os campos da mensagem.
    """
    # Extrai o primeiro byte
    #message_type = (data[0] & 0b11100000) >> 5  # Extrai os 3 bits mais significativos
    #sequence = data[0] & 0b00011111  # Extrai os 5 bits restantes

    if message_type == MESSAGE_TYPES["ATIVA"]:
        agent_id = data[1]
        return {"type": "ATIVA", "sequence": sequence, "agent_id": agent_id}
    elif message_type == MESSAGE_TYPES["ACK"]:
        return {"type": "ACK", "sequence": sequence}
    elif message_type == MESSAGE_TYPES["TASK"]:
        task_type = data[1]
        metric = data[2]
        value = data[3]
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
    ativa_msg = create_ativa_message(5, 42)
    print("Mensagem ATIVA:", ativa_msg, decode_message(ativa_msg))

    # Testando mensagem ACK
    ack_msg = create_ack_message(10)
    print("Mensagem ACK:", ack_msg, decode_message(ack_msg))

    # Testando mensagem TASK
    task_msg = create_task_message(15, 2, 3, 100)
    print("Mensagem TASK:", task_msg, decode_message(task_msg))
