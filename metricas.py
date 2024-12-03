import time
import psutil
import subprocess
import re

def ping_and_store(host, count):
    try:
        result = subprocess.run(
            ["ping", host, "-c", str(count)],
            text=True, capture_output=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Erro ao executar ping: {result.stderr.strip()}")
        
        output = result.stdout
        
        time_regex = r"time=(\d+\.\d+) ms"
        loss_regex = r"(\d+)% packet loss"
        stats_regex = r"min/avg/max/mdev = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)"
        
        times = [float(match) for match in re.findall(time_regex, output)]
        loss = re.search(loss_regex, output)
        stats = re.search(stats_regex, output)
        
        data = {
            "times": times,
            "packet_loss": float(loss.group(1)) if loss else None,
            "min_time": float(stats.group(1)) if stats else None,
            "avg_time": float(stats.group(2)) if stats else None,
            "max_time": float(stats.group(3)) if stats else None,
            "mdev_time": float(stats.group(4)) if stats else None,
        }
        
        # Retornar os dados em vez de apenas imprimir
        return data
    
    except Exception as e:
        print(f"Erro: {e}")
        return None  # Retorna None em caso de erro para não afetar o fluxo

        

import subprocess
import re

def iperf_and_store(server, port, duration):
    try:
        # Executa o iperf3 no modo cliente
        result = subprocess.run(
            ["iperf3", "-c", server, "-p", str(port), "-t", str(duration)],
            text=True,
            capture_output=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Erro ao executar iperf: {result.stderr.strip()}")
        
        output = result.stdout

        # Regex para capturar largura de banda e transferência
        bandwidth_regex = r"(\d+\.\d+|\d+) (Mbits/sec|Gbits/sec)"
        transfer_regex = r"(\d+\.\d+|\d+) (MBytes|GBytes)"

        # Captura largura de banda (última ocorrência no log)
        final_stats = re.findall(bandwidth_regex, output)
        transfers = re.findall(transfer_regex, output)
        
        # Processa a largura de banda
        if final_stats:
            bandwidth_value, bandwidth_unit = final_stats[-1]
            bandwidth = float(bandwidth_value)
            if bandwidth_unit == "Gbits/sec":
                bandwidth *= 1000  # Converte para Mbits/sec
        else:
            bandwidth = None

        # Processa a transferência
        if transfers:
            transfer_value, transfer_unit = transfers[-1]
            transfer = float(transfer_value)
            if transfer_unit == "GBytes":
                transfer *= 1000  # Converte para MBytes
        else:
            transfer = None

        # Dados processados
        data = {
            "server": server,
            "port": port,
            "duration": duration,
            "bandwidth_mbps": bandwidth,
            "transfer_mbytes": transfer
        }
        
        return data

    except Exception as e:
        print(f"Erro: {e}")
        return None  # Retorna None em caso de erro


        
def get_cpu_usage(interval):
    try:
        cpu_usage = psutil.cpu_percent(interval=interval)
        return cpu_usage  # Retornar o valor da CPU
    except Exception as e:
        print(f"Erro ao obter o uso da CPU: {e}")
        return None  # Retornar None em caso de erro


def collect_cpu_usage():
        """
        Collect real CPU usage using psutil.

        Returns:
            dict: A dictionary containing the CPU usage percentage.
        """
        try:
            cpu_usage = psutil.cpu_percent(interval=1)  # Get CPU usage over a 1-second interval
            return {"status": "success", "cpu_usage": f"{cpu_usage:.2f}%"}
        except Exception as e:
            return {"status": "failure", "error": str(e)}


def get_ram_usage():
    try:
        mem = psutil.virtual_memory()
        ram_usage = {
            "total": mem.total / (1024 ** 3),
            "available": mem.available / (1024 ** 3),
            "used": mem.used / (1024 ** 3),
            "percent": mem.percent
        }
        return ram_usage  # Retornar o dicionário com as informações de RAM
    except Exception as e:
        print(f"Erro ao obter o uso da RAM: {e}")
        return None  # Retornar None em caso de erro

if __name__ == "__main__":
    print("Escolha uma métrica para monitorar continuamente:")
    print("1. Ping")
    print("2. Iperf")
    print("3. Uso da CPU")
    print("4. Uso da RAM")
    choice = input("Opção: ")
    
    if choice == "1":
        result = ping_and_store("10.0.5.10", 4)
        if result:
            print(result)
    elif choice == "2":
        result = iperf_and_store("10.0.0.10", 5201, 10)
        if result:
            print(result)
    elif choice == "3":
        result = collect_cpu_usage()
        if result is not None:
            print(f"Uso da CPU: {result}%")
    elif choice == "4":
        result = get_ram_usage()
        if result:
            print(f"Uso de RAM: {result}")
    else:
        print("Opção inválida.")
