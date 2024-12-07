import struct
import json  # Importação necessária para serialização JSON

# Define os tipos de mensagem
MESSAGE_TYPES = {
    "ATIVA": 0x01,  # Registro
    "ACK": 0x02,    # Confirmação
    "TASK": 0x03,   # Tarefas e métricas
    "REPORT": 0x04, # Relatórios
    "ALERTFLOW": 0x05 # Alertas
}

def create_ativa_message(sequence, agent_id):
    """
    Cria uma mensagem ATIVA com apenas o agent_id.
    """
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
    """
    Decodifica mensagens recebidas.
    """
    message_type = data[0]

    if message_type == MESSAGE_TYPES["ATIVA"]:
        # Decodificar a mensagem ATIVA que contém a porta
        _, sequence, agent_id = struct.unpack("!BBB", data)
        return {"type": "ATIVA", "sequence": sequence, "agent_id": agent_id}
    elif message_type == MESSAGE_TYPES["ACK"]:
        _, sequence = struct.unpack("!BB", data)
        return {"type": "ACK", "sequence": sequence}
    elif message_type == MESSAGE_TYPES["TASK"]:
        sequence = data[1]
        payload = json.loads(data[2:].decode('utf-8'))
        return {"type": "TASK", "sequence": sequence, **payload}
    elif message_type == MESSAGE_TYPES["REPORT"]:
        sequence = data[1]  # Obtém o número de sequência
        report_content = data[2:].decode('utf-8')  # Decodifica o restante da mensagem como string UTF-8
        return {"type": "REPORT", "sequence": sequence, "report": report_content}
    elif message_type == MESSAGE_TYPES["ALERTFLOW"]:
        sequence = data[1]
        alert_content = json.loads(data[2:].decode('utf-8'))
        return {"type": "ALERTFLOW", "sequence": sequence, **alert_content}
    else:
        return {"type": "UNKNOWN", "raw_data": data}
    
# Função para criar uma mensagem ALERTFLOW
def create_alert_message(report, sequence):
    """
    Cria uma mensagem ALERTFLOW específica.
    """
    message_type = MESSAGE_TYPES["ALERTFLOW"]
    report_content = create_report_message(report)  # Usa o mesmo formato de relatório
    return struct.pack("!BB", message_type, sequence) + report_content.encode('utf-8')

def create_alert_message_metric(result, sequence):
    """
    Cria uma mensagem ALERTFLOW baseada em métricas.
    """
    message_type = MESSAGE_TYPES["ALERTFLOW"]
    alert_content = json.dumps(result).encode('utf-8')
    return struct.pack("!BB", message_type, sequence) + alert_content

def create_report_message(report):
    """
    Gera um relatório detalhado a partir do objeto report e retorna como string formatada.
    """
    try:
        # Cabeçalho do relatório
        report_content = []
        report_content.append(f"{' Relatorio da Tarefa ':*^50}")
        report_content.append(f"ID da Tarefa: {report.get('task_id')}")
        report_content.append(f"Status: {report.get('status')}\n")

        # Detalhes dos resultados
        report_content.append("Resultados Detalhados:\n")

        for i, result in enumerate(report.get('results'), start=1):
            report_content.append(f"{' Tentativa ' + str(i) + ' ':=^50}")

            if "ping" in result:
                ping = result["ping"]
                report_content.append("🏓 Ping:")
                report_content.append(f"  Host: {ping.get('host')}")
                report_content.append(f"  Tempos (ms): {ping.get('times', [])}")
                report_content.append(f"  Perda de Pacotes: {ping.get('packet_loss')}%")
                report_content.append(f"  Tempo Maximo: {ping.get('max_time', 'N/A')} ms")
                report_content.append(f"  Tempo Minimo: {ping.get('min_time', 'N/A')} ms")
                report_content.append(f"  Tempo Medio: {ping.get('avg_time', 'N/A')} ms\n")

            if "iperf" in result:
                iperf = result["iperf"]
                report_content.append(" Iperf:")
                report_content.append(f"  Servidor: {iperf.get('server')}")
                report_content.append(f"  Largura de Banda: {iperf.get('bandwidth_mbps', 'N/A')} Mbps")
                report_content.append(f"  Transferesncia: {iperf.get('transfer_mbytes', 'N/A')} MB\n")

            if "cpu" in result:
                report_content.append(f" CPU Uso: {result['cpu']}%\n")

            if "ram" in result:
                ram = result["ram"]
                report_content.append(" RAM:")
                report_content.append(f"  Total: {ram.get('total', 'N/A')} GB")
                report_content.append(f"  Usado: {ram.get('used', 'N/A')} GB")
                report_content.append(f"  Percentual de Uso: {ram.get('percent', 'N/A')}%\n")

        # Adicionar erros (se houver)
        if report.get("status") == "failed":
            report_content.append(f"{' ERRO ':!^50}")
            report_content.append(f"Detalhes do Erro: {report.get('error', 'N/A')}")

        # Rodapé
        report_content.append(f"{' Fim do Relatorio ':*^50}")

        # Combinar tudo em uma string formatada
        return "\n".join(report_content)
    except Exception as e:
        print(f"[ERROR] Falha ao criar a mensagem de relatorio: {e}")
        return ""



def create_serialized_report_message(sequence, report):
        # Obter o tipo de mensagem
        message_type = MESSAGE_TYPES["REPORT"]

        # Gerar o conteúdo do relatório como string
        report_content = create_report_message(report)  # Usa a função existente

        # Serializar a mensagem combinando tipo, sequência e conteúdo
        return struct.pack("!BB", message_type, sequence) + report_content.encode('utf-8')
    