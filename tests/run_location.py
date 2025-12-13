import os
import time
import socket
import argparse
from location.location_node import LocationNode  # ...existing code...
from app.discovery import NodeType

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="ID del LocationNode")
    parser.add_argument("--port", type=int, required=True, help="Puerto de escucha")
    parser.add_argument("--type", required=True, choices=[t.value for t in NodeType], help="Tipo de nodo (ROUTING/PROCESSING/DATA/AUTH)")
    parser.add_argument("--subnet", default=None, help="DISCOVERY_SUBNET (opcional)")
    parser.add_argument("--discover-interval", type=int, default=5, help="Intervalo entre prints/queries")
    args = parser.parse_args()

    if args.subnet:
        os.environ["DISCOVERY_SUBNET"] = args.subnet

    ip_local = socket.gethostbyname(socket.gethostname())
    node_type = NodeType(args.type)

    print(f"[INFO] Iniciando LocationNode '{args.id}' ({node_type.value}) en {ip_local}:{args.port} (subnet={os.getenv('DISCOVERY_SUBNET')})")

    node = LocationNode(node_name=args.id, ip=ip_local, port=args.port, node_type=node_type)

    try:
        # pequeño loop para mostrar descubrimiento / registro / resolver nodos
        while True:
            time.sleep(args.discover_interval)
            with node.discovery_nodes_lock:
                print(f"[DISCOVERED_DISCOVERIES] {node.discovery_nodes}")

            # Probar query_by_name y query_by_role
            result_by_name = node.query_by_name("location2")
            print(f"[QUERY_BY_NAME 'location2'] {result_by_name}")

            result_by_role = node.query_by_role(NodeType.ROUTING)
            print(f"[QUERY_BY_ROLE 'ROUTING'] {result_by_role}")
            
    except KeyboardInterrupt:
        print("[INFO] Deteniendo LocationNode")
        node.stop_server()

if __name__ == "__main__":
    main()