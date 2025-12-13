import argparse
from comm import CommunicationNode, Message

parser = argparse.ArgumentParser()
parser.add_argument("--id", required=True, help="ID del nodo emisor")
parser.add_argument("--target", required=True, help="ID o hostname del nodo receptor")
parser.add_argument("--port", type=int, required=True, help="Puerto del nodo receptor")
args = parser.parse_args()

node = CommunicationNode(node_name=args.id, ip="0.0.0.0", port=0)  # puerto 0 = no servidor, solo cliente

msg = Message(type="PING", src=args.id, dst=args.target, payload={"msg": "hello"})
response = node.send_message(args.target, args.port, msg, await_response=True)
print(f"[{args.id}] Recibida respuesta: {response.payload if response else None}")
