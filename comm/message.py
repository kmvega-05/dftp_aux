import json
import time
import uuid

class Message:
    def __init__(self, type: str, src: str, dst: str = None, payload: dict = None,
                 metadata: dict = None):
        """
        Inicializa un mensaje con header, payload y metadata.
        type: tipo de mensaje, por ejemplo "DATA_READ"
        src: id del nodo origen
        dst: id del nodo destino (opcional)
        payload: contenido del mensaje
        metadata: diccionario opcional, si no se pasa se genera msg_id y timestamp automáticamente
        """
        self.header = {
            "type": type,
            "src": src,
            "dst": dst
        }
        self.payload = payload or {}
        self.metadata = metadata or {
            "msg_id": str(uuid.uuid4()),
            "timestamp": int(time.time())
        }

    def to_json(self) -> str:
        """
        Serializa el mensaje a JSON terminado en '\n', listo para enviar por TCP.
        """
        return json.dumps({
            "header": self.header,
            "payload": self.payload,
            "metadata": self.metadata
        }) + "\n"

    @staticmethod
    def from_json(raw: str) -> "Message":
        """
        Deserializa un JSON recibido y devuelve un objeto Mensaje.
        """
        data = json.loads(raw)
        return Message(
            type=data["header"]["type"],
            src=data["header"]["src"],
            dst=data["header"].get("dst"),
            payload=data.get("payload"),
            metadata=data.get("metadata")
        )

    def __repr__(self):
        return f"Mensaje(type={self.header['type']}, src={self.header['src']}, dst={self.header.get('dst')}, payload={self.payload})"
