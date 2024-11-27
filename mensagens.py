import struct
import json  # Importação necessária para serialização JSON

# Define os tipos de mensagem
MESSAGE_TYPES = {
    "ATIVA": 0x01,  # Registro
    "ACK": 0x02,    # Confirmação
    "TASK": 0x03,   # Tarefas e métricas
}

# Função para criar uma mensagem ATIVA
def create_ativa_message(sequence, agent_id):
    message_type = MESSAGE_TYPES["ATIVA"]
    return struct.pack("!BBB", message_type, sequence, agent_id)

# Função para criar uma mensagem ACK
def create_ack_message(sequence):
    message_type = MESSAGE_TYPES["ACK"]
    return struct.pack("!BB", message_type, sequence)

# Função para criar uma mensagem TASK
def create_task_message(sequence, metrics, link_metrics, alert_conditions):
    """
    Cria uma mensagem de tarefa (TASK) em binário.
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

# Função para decodificar mensagens
def decode_message(data):
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
