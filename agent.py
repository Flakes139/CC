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
    tcp_port = 44444
    agent_id = int(input("Digite o ID do agente: ").strip())
    return server_ip, udp_port, tcp_port, agent_id


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

def send_tcp_message(server_ip, tcp_port, message, max_attempts=3):
    """
    Envia uma mensagem via TCP para o servidor e espera por uma resposta.
    Inclui lógica para reconexão em caso de falhas.
    """
    for attempt in range(max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
                tcp_sock.settimeout(3)  # Timeout de 3 segundos
                tcp_sock.connect((server_ip, tcp_port))
                print(f"[TCP] Conectado ao servidor TCP em {server_ip}:{tcp_port} (Tentativa {attempt + 1})")

                # Enviar a mensagem
                tcp_sock.sendall(message)
                print(f"[TCP] Mensagem enviada: {mensagens.decode_message(message)}")

                # Receber a resposta
                ack = tcp_sock.recv(1024)
                decoded_response = mensagens.decode_message(ack)
                print(f"[TCP] Resposta do servidor: {decoded_response}")

                return decoded_response  # Sucesso
        except (socket.timeout, Exception) as e:
            print(f"[TCP] Erro na comunicação TCP (Tentativa {attempt + 1}): {e}")
            time.sleep(3)  # Esperar antes de tentar novamente

    print("[TCP] Falha após todas as tentativas de conexão.")
    return None

def send_alertflow_metric(sock, server_address, result, alert_condition, tcp_port, sequence):
    """
    Envia um alertflow ao servidor.
    """
    if isinstance(result, (int, float)):
        result = {"value": result}  # Transformar em dicionário se for um número

    result["alert_condition"] = alert_condition  # Adicionar a condição de alerta
    alert_message = mensagens.create_alert_message_metric(result,sequence)

    # Enviar o alertflow via TCP
    response = send_tcp_message(server_address[0], tcp_port, alert_message)  # Corrigido para usar server_address[0]
    if response:
        print(f"[ALERTFLOW - TCP] Alertflow enviado e resposta recebida: {response}")
    else:
        print("[ALERTFLOW - TCP] Falha ao enviar alertflow.")


def send_alertflow(sock, server_address, report, tcp_port, sequence):
    """
    Envia um alertflow ao servidor.
    """
    alert_message = mensagens.create_alert_message(report, sequence)
    response = send_tcp_message(server_address[0], tcp_port, alert_message)
    if response: 
        print(f"[ALERTFLOW - TCP] Alertflow enviado com sucesso: {response}")
    else:
        print("[ALERTFLOW - TCP] Falha ao enviar alertflow.")

def process_task(sock, server_address, task, alertflow_count, tcp_port):
    """
    Processa a tarefa recebida e realiza as metricas.
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
                if int(result["ping"].get('avg_time', 'N/A')) > alert_conditions["latency"] :
                    send_alertflow_metric(sock, server_address, result["ping"].get('avg_time', 'N/A'), alert_conditions["latency"], tcp_port, sequence)
                    alertflow_count = alertflow_count + 1

            if "bandwidth" in link_metrics:
                print(f"[TASK] Realizando iperf ({attempt}/3)...")
                result["iperf"] = metricas.iperf_and_store(
                    link_metrics["bandwidth"]["iperf"].get("server"),
                    link_metrics["bandwidth"]["iperf"].get("port"),
                    link_metrics["bandwidth"]["iperf"].get("duration")
                )
                if int(result["iperf"].get('bandwidth_mbps', 'N/A')) < alert_conditions["bandwidth"] : 
                    send_alertflow_metric(sock, server_address, result["iperf"].get('bandwidth_mbps', 'N/A'), alert_conditions["bandwidth"], tcp_port,sequence )
                    alertflow_count = alertflow_count + 1

            if metrics.get("cpu_usage") == True:
                print(f"[TASK] Monitorando CPU ({attempt}/3)...")
                result["cpu"] = metricas.collect_cpu_usage()
                if int(result["cpu"]) > alert_conditions["cpu_usage"] :
                    send_alertflow_metric(sock, server_address,result["cpu"],alert_conditions["cpu_usage"], tcp_port,sequence)
                    alertflow_count = alertflow_count + 1

            if metrics.get("ram_usage") == True:
                print(f"[TASK] Monitorando RAM ({attempt}/3)...")
                result["ram"] = metricas.get_ram_usage()
                if int(result["ram"].get('percent', 'N/A')) > alert_conditions["ram_usage"] :
                    send_alertflow_metric(sock, server_address, result["ram"].get('percent', 'N/A'),alert_conditions["ram_usage"], tcp_port,sequence)
                    alertflow_count = alertflow_count + 1

            results.append(result)  # Adiciona o resultado desta tentativa à lista de resultados
            time.sleep(5)

        # Criar o relatório final após as tentativas
    
        report = {"task_id": task_id, "results": results, "status": "success"}
    except Exception as e:
        print(f"[TASK] Falha na tarefa {task_id}: {e}")
        report = {"task_id": task_id, "results": results, "status": "failed", "error": str(e)}

    # Avaliar as condições de alerta
    if report["status"] == "failed":
        send_alertflow(sock, server_address, report, tcp_port,sequence)
        alertflow_count += 1
    else:
       send_report(sock, server_address, report, sequence)
        
    return alertflow_count
 
def send_report(sock, server_address, report,sequence):
    """
    Envia o relatório final ao servidor.
    """
    try:
        report_message_final = mensagens.create_serialized_report_message(sequence, report)
        sock.sendto(report_message_final, server_address)
        print(f"[REPORT] Relatório enviado: \n {report_message_final}")
    except Exception as e:
        print(f"[REPORT] Erro ao enviar o relatório: {e}")




def udp_receiver(sock, server_address, tcp_port):
    """
    Recebe mensagens do servidor via UDP e processa as tarefas de maneira sequencial,
    executando continuamente até que outra mensagem seja recebida.
    """
    print(f"[UDP] Cliente ouvindo na porta UDP {sock.getsockname()[1]}")

    current_task = None  # Para armazenar a tarefa atual
    alertflow_count = 0


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
            if current_task and alertflow_count<3 :
                alertflow_count += process_task(sock, server_address, current_task, 0, tcp_port)
                if alertflow_count >= 3 :
                    print("Terceiro Alertflow : Terminar agente")
                    sock.close()
                    break
                time.sleep(10)

        except Exception as e:
            print(f"[UDP] Erro ao processar mensagem: {e}")



if __name__ == "__main__":
    server_ip, udp_port, tcp_port, agent_id = initialize_agent()

    # Criar uma única socket para todo o ciclo de vida do agente
    agent_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    agent_socket.bind(('', 33333))  # Porta fixa para o agente

    # Registrar o agente
    if register_agent(agent_socket, server_ip, udp_port, agent_id):
        # O valor de server_address é o IP e porta do servidor
        server_address = (server_ip, udp_port)

        # Iniciar o receptor UDP somente se o registro foi bem-sucedido
        udp_receiver_thread = Thread(target=udp_receiver, args=(agent_socket, server_address, tcp_port), daemon=True)
        udp_receiver_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Agente] Encerrado.")
            agent_socket.close()


