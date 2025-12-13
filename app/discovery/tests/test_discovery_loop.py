import os
import time
import socket
import argparse
from app.discovery import DiscoveryNode

def main():
    parser = argparse.ArgumentParser(description="Run a DiscoveryNode")
    parser.add_argument("--name", required=True, help="Node ID del discovery node")
    args = parser.parse_args()

    # Configurar subnet
    os.environ["DISCOVERY_SUBNET"] = "172.30.0.0/28"

    # Obtener IP local
    ip_local = socket.gethostbyname(socket.gethostname())

    print(f"[INFO] Iniciando DiscoveryNode '{args.name}' en {ip_local}:9100")

    node = DiscoveryNode(
        node_name=args.name,
        ip=ip_local,
        port=9100,
        testing=False
    )

    print("[INFO] Esperando 60 segundos para descubrimiento...")
    time.sleep(60)

    print("\n[INFO] Peers descubiertos:")
    with node.peers_lock:
        print(node.peers)


if __name__ == "__main__":
    main()
