import os
import time
import socket
import argparse
from app.discovery import DiscoveryNode

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="ID del DiscoveryNode")
    parser.add_argument("--port", type=int, default=9100, help="Puerto de escucha")
    parser.add_argument("--subnet", default=None, help="DISCOVERY_SUBNET (opcional)")
    parser.add_argument("--peer-interval", type=int, default=10, help="peer_discovery_interval seconds")
    args = parser.parse_args()

    if args.subnet:
        os.environ["DISCOVERY_SUBNET"] = args.subnet

    # Obtener ip del contenedor
    ip_local = socket.gethostbyname(socket.gethostname())

    print(f"[INFO] Iniciando DiscoveryNode '{args.name}' en {ip_local}:{args.port} (subnet={os.getenv('DISCOVERY_SUBNET')})")

    node = DiscoveryNode(node_name=args.name, ip=ip_local, port=args.port, discovery_interval=args.peer_interval, testing=False)
    
    try:
        while True:
            time.sleep(5)
            
            with node.peers_lock:
                print(f"[PEERS] {node.peers}")

            nodes = node.register_table.get_all_nodes()
            print(f"[REGISTERED] {[n.to_dict() for n in nodes]}")
    
    except KeyboardInterrupt:
        print("[INFO] Deteniendo DiscoveryNode")
        node.stop_server()

if __name__ == "__main__":
    main()