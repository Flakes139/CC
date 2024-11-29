import struct
import json  # Importação necessária para serialização JSON

# Define os tipos de mensagem
MESSAGE_TYPES = {
    "ATIVA": 0x01,  # Registro
    "ACK": 0x02,    # Confirmação
    "TASK": 0x03,   # Tarefas e métricas
}

# Função para criar uma mensagem ATIVA
def create_ativa_message(sequence, agent_id, agent_port):
    """
    Cria uma mensagem ATIVA com o agent_id e agent_port.
    """
    message_type = MESSAGE_TYPES["ATIVA"]
    # Empacota o tipo, sequência, ID do agente e a porta do agente
    return struct.pack("!BBBH", message_type, sequence, agent_id, agent_port)


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
    """
    Decodifica mensagens recebidas.
    """
    message_type = data[0]

    if message_type == MESSAGE_TYPES["ATIVA"]:
        # Decodificar a mensagem ATIVA que contém a porta
        _, sequence, agent_id, agent_port = struct.unpack("!BBBH", data)
        return {"type": "ATIVA", "sequence": sequence, "agent_id": agent_id, "agent_port": agent_port}
    elif message_type == MESSAGE_TYPES["ACK"]:
        _, sequence = struct.unpack("!BB", data)
        return {"type": "ACK", "sequence": sequence}
    elif message_type == MESSAGE_TYPES["TASK"]:
        sequence = data[1]
        payload = json.loads(data[2:].decode('utf-8'))
        return {"type": "TASK", "sequence": sequence, **payload}
    else:
        return {"type": "UNKNOWN", "raw_data": data}
