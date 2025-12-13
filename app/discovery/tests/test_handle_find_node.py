import unittest
import os
from app.discovery import DiscoveryNode, ServiceRegister, NodeType
from comm import Message

class TestDiscoveryNodeFindNode(unittest.TestCase):

    def setUp(self):
        # Definir variable de entorno para subnet
        os.environ["DISCOVERY_SUBNET"] = "192.168.1.0/24"

        # Crear DiscoveryNode en modo testing
        self.node = DiscoveryNode(
            node_name="discovery1",
            ip="192.168.1.101",
            port=9100,
            testing=True
        )
        print("[Setup] DiscoveryNode creado para testing")

    def test_find_node(self):
        # Consultar un nodo que no existe
        msg = Message(
            type="DISCOVERY_FIND_NODE",
            src="192.168.1.102",
            dst=self.node.ip,
            payload={}
        )

        response = self.node._on_message(msg, None)

        self.assertIsNotNone(response)

        self.assertIn("status", response.payload)
        self.assertIn("name", response.payload)
        self.assertIn("ip", response.payload)

        self.assertEqual(response.payload["status"], "OK")
        self.assertEqual(response.payload["name"], self.node.node_name)
        self.assertEqual(response.payload["ip"], self.node.ip)

        #chequear destinatario
        self.assertIn("dst", response.header)
        self.assertEqual(response.header["dst"], msg.header["src"])

        print(f"[Info] Respuesta enviada: {response}")
        print("[Test] Test query_find_node completado exitosamente.")

if __name__ == "__main__":
    print("[Main] Iniciando tests de DiscoveryNode find_node...")
    unittest.main()
    print("[Main] Todos los tests completados")