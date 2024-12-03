import socket
import time
from threading import Thread
import mensagens
import metricas 

def initialize_agent():
    """
    Solicita ao usuário o IP do servidor, porta UDP e ID do agente.
    """
    server_ip = input("Digite o IP do servidor: ").strip()
    udp_port = 33333
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

def process_task(sock, server_address, task):
    """
    Processa a tarefa recebida e realiza as métricas.
    Envia um relatório final ou alertflow ao servidor.
    """
    sequence = task.get("sequence")

    task_id = task.get("sequence")
    metrics = task.get("metrics")
    link_metrics = task.get("link_metrics")
    alert_conditions = task.get("alert_conditions")

    results = []
    try:
        for attempt in range(1, 4):  # Loop de tentativas
            result = {}

            # Executar métricas (ping, iperf, etc.)
            if "latency" in link_metrics:
                print(f"[TASK] Realizando ping ({attempt}/3)...")
                result["ping"] = metricas.ping_and_store(
                    link_metrics["latency"]["ping"]["destination"],
                    link_metrics["latency"]["ping"]["count"]
                )

            if "bandwidth" in link_metrics:
                print(f"[TASK] Realizando iperf ({attempt}/3)...")
                result["iperf"] = metricas.iperf_and_store(
                    link_metrics["bandwidth"]["iperf"]["server"],
                    link_metrics["bandwidth"]["iperf"].get("port"),
                    link_metrics["bandwidth"]["iperf"].get("duration")
                )

            if metrics.get("cpu_usage") == True:
                print(f"[TASK] Monitorando CPU ({attempt}/3)...")
                result["cpu"] = metricas.get_cpu_usage(3)

            if metrics.get("ram_usage") == True:
                print(f"[TASK] Monitorando RAM ({attempt}/3)...")
                result["ram"] = metricas.get_ram_usage()

            results.append(result)  # Adiciona o resultado desta tentativa à lista de resultados
            time.sleep(5)

        # Criar o relatório final após as tentativas
        report = {"task_id": task_id, "results": results, "status": "success"}

    except Exception as e:
        print(f"[TASK] Falha na tarefa {task_id}: {e}")
        report = {"task_id": task_id, "results": results, "status": "failed", "error": str(e)}

    # Avaliar as condições de alerta
    if report["status"] == "failed" or any(evaluate_alert_conditions(alert_conditions, r) for r in report["results"]):
        send_alertflow(sock, server_address, report)
    else:
        send_report(sock, server_address, report, sequence)



def evaluate_alert_conditions(conditions, result):
    """
    Avalia se as condições de alerta são atendidas.
    """
    try:
        # Exemplo: Verificar se o tempo médio de ping é maior que um limite
        if "ping" in result and "max_time" in result["ping"]:
            if result["ping"]["max_time"] > conditions.get("max_ping_time", float('inf')):
                return True
        # Outras condições podem ser adicionadas aqui
    except Exception as e:
        print(f"[ALERT] Erro ao avaliar condição de alerta: {e}")
    return False

def send_alertflow(sock, server_address, report):
    """
    Envia um alertflow ao servidor.
    """
    alert_message = mensagens.create_alert_message(report)
    sock.sendto(alert_message, server_address)
    print(f"[ALERTFLOW] Enviado: {report}")

def send_report(sock, server_address, report,sequence):
    """
    Envia o relatório final ao servidor.
    """
    try:
        report_message = mensagens.create_report_message(report)  # String formatada
        report_message_final = mensagens.create_serialized_report_message(sequence, report_message) 
        sock.sendto(report_message_final, server_address)
        print(f"[REPORT] Relatório enviado: \n {report_message}")
    except Exception as e:
        print(f"[REPORT] Erro ao enviar o relatório: {e}")



def udp_receiver(sock, server_address):
    """
    Recebe mensagens do servidor via UDP e processa as tarefas de maneira sequencial,
    executando continuamente até que outra mensagem seja recebida.
    """
    print(f"[UDP] Cliente ouvindo na porta UDP {sock.getsockname()[1]}")

    current_task = None  # Para armazenar a tarefa atual

    while True:
        try:
            # Verificar se há uma mensagem nova
            sock.settimeout(1)  # Timeout para evitar bloqueio permanente
            try:
                message, address = sock.recvfrom(1024)
                decoded = mensagens.decode_message(message)
                print(f"[UDP] Mensagem decodificada recebida do servidor: {decoded}")

                if decoded["type"] == "TASK":
                    # Enviar ACK para o servidor
                    ack_message = mensagens.create_ack_message(decoded["sequence"])
                    sock.sendto(ack_message, address)
                    print(f"[UDP] ACK enviado para o servidor em {address}")

                    # Atualizar a tarefa atual
                    current_task = decoded

            except socket.timeout:
                pass  # Continuar caso não haja novas mensagens

            # Continuar processando a tarefa atual, se existir
            if current_task:
                process_task(sock, server_address, current_task)

        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem: {e}")



if __name__ == "__main__":
    server_ip, udp_port, agent_id = initialize_agent()

    # Criar uma única socket para todo o ciclo de vida do agente
    agent_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    agent_socket.bind(('', 33333))  # Porta fixa para o agente

    # Registrar o agente
    if register_agent(agent_socket, server_ip, udp_port, agent_id):
        # O valor de server_address é o IP e porta do servidor
        server_address = (server_ip, udp_port)

        # Iniciar o receptor UDP somente se o registro foi bem-sucedido
        udp_receiver_thread = Thread(target=udp_receiver, args=(agent_socket, server_address), daemon=True)
        udp_receiver_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Agente] Encerrado.")
            agent_socket.close()



