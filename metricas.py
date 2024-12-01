import time
import psutil
import subprocess
import re

def ping_and_store(host, count):
    while True:
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
            
            print("\nResultado do Ping:")
            print(f"  Host: {host}")
            print(f"  Tempos individuais (ms): {data['times']}")
            print(f"  Perda de pacotes: {data['packet_loss']}%")                
            print(f"  Tempo mínimo: {data['min_time']} ms")
            print(f"  Tempo médio: {data['avg_time']} ms")
            print(f"  Tempo máximo: {data['max_time']} ms\n")
            
        except Exception as e:
            print(f"Erro: {e}")
        
        time.sleep(5)

def iperf_and_store(server, port=5201, duration=10):
    while True:
        try:
            result = subprocess.run(
                ["iperf3", "-c", server, "-p", str(port), "-t", str(duration)],
                text=True, capture_output=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Erro ao executar iperf: {result.stderr.strip()}")
            
            output = result.stdout
            
            bandwidth_regex = r"(\d+\.\d+|\d+) (Mbits/sec|Gbits/sec)"
            transfer_regex = r"(\d+\.\d+|\d+) (MBytes|GBytes)"
            
            final_stats = re.findall(r"\[SUM\].*?(\d+\.\d+|\d+) (Mbits/sec|Gbits/sec)", output)
            transfers = re.findall(transfer_regex, output)
            
            if final_stats:
                bandwidth_value, bandwidth_unit = final_stats[-1]
                bandwidth = float(bandwidth_value)
                if bandwidth_unit == "Gbits/sec":
                    bandwidth *= 1000
            else:
                bandwidth = None
            
            if transfers:
                transfer_value, transfer_unit = transfers[-1]
                transfer = float(transfer_value)
                if transfer_unit == "GBytes":
                    transfer *= 1000
            else:
                transfer = None
            
            data = {
                "server": server,
                "port": port,
                "duration": duration,
                "bandwidth_mbps": bandwidth,
                "transfer_mbytes": transfer
            }
            
            print("\nResultado do Iperf:")
            print(f"  Servidor: {server}")
            print(f"  Porta: {port}")
            print(f"  Duração: {duration}s")
            print(f"  Largura de banda: {data['bandwidth_mbps']} Mbits/s")
            print(f"  Transferência: {data['transfer_mbytes']} MB\n")
        
        except Exception as e:
            print(f"Erro: {e}")
        
        time.sleep(5)

def get_cpu_usage(interval):
    while True:
        try:
            cpu_usage = psutil.cpu_percent(interval=interval)
            print(f"\nUso da CPU: {cpu_usage}%\n")
        except Exception as e:
            print(f"Erro ao obter o uso da CPU: {e}")
        
        time.sleep(5)

def get_ram_usage():
    while True:
        try:
            mem = psutil.virtual_memory()
            ram_usage = {
                "total": mem.total / (1024 ** 3),
                "available": mem.available / (1024 ** 3),
                "used": mem.used / (1024 ** 3),
                "percent": mem.percent
            }
            print("\nUso de RAM:")
            print(f"  Total: {ram_usage['total']:.2f} GB")
            print(f"  Disponível: {ram_usage['available']:.2f} GB")
            print(f"  Usado: {ram_usage['used']:.2f} GB")
            print(f"  Percentual de Uso: {ram_usage['percent']}%\n")
        except Exception as e:
            print(f"Erro ao obter o uso da RAM: {e}")
        
        time.sleep(5)

if __name__ == "__main__":
    print("Escolha uma métrica para monitorar continuamente:")
    print("1. Ping")
    print("2. Iperf")
    print("3. Uso da CPU")
    print("4. Uso da RAM")
    choice = input("Opção: ")
    
    if choice == "1":
        ping_and_store("10.0.5.10", 4)
    elif choice == "2":
        iperf_and_store("10.0.5.10", 5201, 10)
    elif choice == "3":
        get_cpu_usage(1)
    elif choice == "4":
        get_ram_usage()
    else:
        print("Opção inválida.")
