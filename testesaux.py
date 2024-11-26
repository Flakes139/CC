import psutil
import subprocess
import re

def ping_and_store(host, count):
    """
    Executa o comando ping para um host especificado, lê os valores e os guarda em um dicionário.
    
    Args:
        host (str): O endereço ou domínio para pingar.
        count (int): Número de pacotes a serem enviados (padrão é 4).
        
    Returns:
        dict: Contém os valores extraídos, como tempos médios, mínimo, máximo e perda de pacotes.
    """
    try:
        # Executa o comando ping3
        
        result = subprocess.run(
            ["ping", host, "-c", str(count)],  # Para Windows, substitua "-c" por "-n"
            text=True, capture_output=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Erro ao executar ping: {result.stderr.strip()}")
        
        # Analisando a saída
        output = result.stdout
        
        # Regex para capturar os tempos e perda de pacotes
        time_regex = r"time=(\d+\.\d+) ms"
        loss_regex = r"(\d+)% packet loss"
        stats_regex = r"min/avg/max/mdev = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)"
        
        times = [float(match) for match in re.findall(time_regex, output)]
        loss = re.search(loss_regex, output)
        stats = re.search(stats_regex, output)
        
        # Montando o dicionário com os dados
        data = {
            "times": times,
            "packet_loss": float(loss.group(1)) if loss else None,
            "min_time": float(stats.group(1)) if stats else None,
            "avg_time": float(stats.group(2)) if stats else None,
            "max_time": float(stats.group(3)) if stats else None,
            "mdev_time": float(stats.group(4)) if stats else None,
        }

        print("\nResultado do Ping:")
        print(f"  Host: {host}")
        print(f"  Tempos individuais (ms): {data['times']}")
        print(f"  Perda de pacotes: {data['packet_loss']}%")                
        print(f"  Tempo mínimo: {data['min_time']} ms")
        print(f"  Tempo médio: {data['avg_time']} ms")
        print(f"  Tempo máximo: {data['max_time']} ms")
        print()
    
    except Exception as e:
        print(f"Erro: {e}")
        return None

def iperf_and_store(server: str, port: int = 5201, duration: int = 10):
    """
    Executa o comando iperf, lê os valores e os guarda em um dicionário.
    
    Args:
        server (str): Endereço ou IP do servidor iperf.
        port (int): Porta do servidor iperf (padrão é 5201).
        duration (int): Duração do teste em segundos (padrão é 10).
        
    Returns:
        dict: Contém os valores extraídos, como largura de banda e transferência.
    """
    try:
        # Executa o comando iperf
        result = subprocess.run(
            ["iperf3", "-c", server, "-p", str(port), "-t", str(duration)],
            text=True, capture_output=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Erro ao executar iperf: {result.stderr.strip()}")
        
        # Analisando a saída
        output = result.stdout
        
        # Regex para capturar os valores importantes
        bandwidth_regex = r"(\d+\.\d+|\d+) (Mbits/sec|Gbits/sec)"
        transfer_regex = r"(\d+\.\d+|\d+) (MBytes|GBytes)"
        
        # Procurar pelas estatísticas finais de largura de banda e transferência
        final_stats = re.findall(r"\[SUM\].*?(\d+\.\d+|\d+) (Mbits/sec|Gbits/sec)", output)
        transfers = re.findall(transfer_regex, output)
        
        # Converte os valores para uma estrutura
        if final_stats:
            bandwidth_value, bandwidth_unit = final_stats[-1]
            bandwidth = float(bandwidth_value)
            if bandwidth_unit == "Gbits/sec":
                bandwidth *= 1000  # Convertendo para Mbits/sec
        else:
            bandwidth = None
        
        if transfers:
            transfer_value, transfer_unit = transfers[-1]
            transfer = float(transfer_value)
            if transfer_unit == "GBytes":
                transfer *= 1000  # Convertendo para MBytes
        else:
            transfer = None
        
        # Montando o dicionário com os dados
        data = {
            "server": server,
            "port": port,
            "duration": duration,
            "bandwidth_mbps": bandwidth,  # Em Mbits/sec
            "transfer_mbytes": transfer  # Em MBytes
        }

        print("\nResultado do Iperf:")
        print(f"  Servidor: {server}")
        print(f"  Porta: {port}")
        print(f"  Duração: {duration}s")
        print(f"  Largura de banda: {data['bandwidth_mbps']} Mbits/s")
        print(f"  Transferência: {data['transfer_mbytes']} MB")
        print()
    
    except Exception as e:
        print(f"Erro: {e}")
        return None


def get_cpu_usage(interval):
    """
    Obtém o uso da CPU em porcentagem.
    
    Args:
        interval (float): Intervalo de medição em segundos (padrão: 1 segundo).
        
    Returns:
        float: Uso da CPU em porcentagem.
    """
    try:
        # Obtém o uso da CPU, calculado como a média de todas as CPUs
        cpu_usage = psutil.cpu_percent(interval=interval)
        print(f"\nUso da CPU: {cpu_usage}%\n")

    except Exception as e:
        print(f"Erro ao obter o uso da CPU: {e}")
        return None

def get_ram_usage():
    """
    Obtém informações sobre o uso da memória RAM.
    
    Returns:
        dict: Contém o uso total, disponível, usado e percentual de uso da RAM.
    """
    try:
        # Obtém as informações de memória
        mem = psutil.virtual_memory()
        
        # Monta um dicionário com os dados relevantes
        ram_usage = {
            "total": mem.total / (1024 ** 3),  # Convertendo para GB
            "available": mem.available / (1024 ** 3),  # Convertendo para GB
            "used": mem.used / (1024 ** 3),  # Convertendo para GB
            "percent": mem.percent  # Percentual de uso
        }
        if ram_usage:
                print("\nUso de RAM:")
                print(f"  Total: {ram_usage['total']:.2f} GB")
                print(f"  Disponível: {ram_usage['available']:.2f} GB")
                print(f"  Usado: {ram_usage['used']:.2f} GB")
                print(f"  Percentual de Uso: {ram_usage['percent']}%\n")

    except Exception as e:
        print(f"Erro ao obter o uso da RAM: {e}")
        return None

def main():
    print("Bem-vindo ao monitor de rede e sistema!\n")
    while True:
        print("Escolha uma opção:")
        print("1. Testar ping")
        print("2. Testar iperf")
        print("3. Ver uso da CPU")
        print("4. Ver uso da RAM")
        print("0. Sair")
        choice = input("Opção: ")
        
        if choice == "1":
            ping_and_store("10.0.5.10", 4)

        
        elif choice == "2":         
            iperf_and_store("10.0.5.10", 5201, 10)
        
        elif choice == "3":
            get_cpu_usage(1)
        
        elif choice == "4":
            get_ram_usage()
        
        elif choice == "0":
            print("Saindo...")
            break
        
        else:
            print("Opção inválida. Tente novamente.\n")

if __name__ == "__main__":
    main()