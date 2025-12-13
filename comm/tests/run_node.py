import argparse
import time
from comm import CommunicationNode, Message

parser = argparse.ArgumentParser()
parser.add_argument("--id", required=True, help="ID del nodo")
parser.add_argument("--port", type=int, required=True, help="Puerto a escuchar")
args = parser.parse_args()

def ping_handler(msg, sock):
    print(f"[{args.id}] Recibido PING de {msg.header['src']}: {msg.payload}")
    return Message(
        type="PONG",
        src=args.id,
        dst=msg.header["src"],
        payload={"msg": f"pong from {args.id}"}
    )

node = CommunicationNode(node_name=args.id, ip="0.0.0.0", port=args.port)
node.register_handler("PING", ping_handler)
node.start_server()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    node.stop_server()
