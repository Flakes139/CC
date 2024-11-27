import json

# Caminho para o ficheiro JSON
caminho_ficheiro = "teste.json"

# Função para carregar o ficheiro JSON
def carregar_json(caminho_ficheiro):
    try:
        with open(caminho_ficheiro, 'r', encoding='utf-8') as ficheiro:
            return json.load(ficheiro)
    except FileNotFoundError:
        print(f"Erro: Ficheiro '{caminho_ficheiro}' não encontrado.")
        return None
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar o JSON: {e}")
        return None

# Função para processar as tarefas do JSON
def processar_tarefas(dados):
    if not dados or "tasks" not in dados:
        print("Nenhuma tarefa encontrada no ficheiro JSON.")
        return

    # Iterar sobre as tarefas
    for task in dados["tasks"]:
        print(f"\n--- Tarefa: {task['task_id']} ---")
        print(f"Frequência: {task['frequency']} segundos")

        # Iterar sobre os dispositivos
        for device in task["devices"]:
            print(f"\nDispositivo ID: {device['device_id']}")

            # Métricas do dispositivo
            print("Métricas do dispositivo:")
            device_metrics = device.get("device_metrics", {})
            print(f"  - CPU Uso: {device_metrics.get('cpu_usage', False)}")
            print(f"  - RAM Uso: {device_metrics.get('ram_usage', False)}")
            print(f"  - Interfaces Monitoradas: {', '.join(device_metrics.get('interface_stats', []))}")

            # Métricas de link
            print("Métricas de link:")
            link_metrics = device.get("link_metrics", {})
            for metric, config in link_metrics.items():
                if "iperf" in config:
                    iperf = config["iperf"]
                    print(f"  - {metric.capitalize()} (iperf):")
                    print(f"      * Papel: {iperf.get('role')}")
                    print(f"      * Endereço do Servidor: {iperf.get('server_address', 'N/A')}")
                    print(f"      * Duração do Teste: {iperf.get('test_duration')} segundos")
                    print(f"      * Frequência: {iperf.get('frequency')} segundos")
                if "ping" in config:
                    ping = config["ping"]
                    print(f"  - Latência (ping):")
                    print(f"      * Destino: {ping.get('destination')}")
                    print(f"      * Número de Pacotes: {ping.get('packet_count')}")
                    print(f"      * Frequência: {ping.get('frequency')} segundos")

            # Condições de alerta
            print("Condições de alerta:")
            alert_conditions = device.get("alertflow_conditions", {})
            for condition, threshold in alert_conditions.items():
                print(f"  - {condition.replace('_', ' ').capitalize()}: {threshold}")


# Carregar e processar o ficheiro JSON
dados = carregar_json(caminho_ficheiro)
if dados:
    processar_tarefas(dados)

def carregar_tarefas(caminho_ficheiro):
    """
    Carrega as tarefas do arquivo JSON.
    """
    try:
        with open(caminho_ficheiro, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("tasks", [])[0]["devices"]
    except Exception as e:
        print(f"[Erro] Falha ao carregar o JSON: {e}")
        return []
