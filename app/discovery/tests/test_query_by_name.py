import unittest
import os
from app.discovery import DiscoveryNode, ServiceRegister, NodeType
from comm import Message

class TestDiscoveryNodeQueryByName(unittest.TestCase):

    def setUp(self):
        # Definir variable de entorno para subnet
        os.environ["DISCOVERY_SUBNET"] = "192.168.1.0/24"

        # Crear DiscoveryNode en modo testing
        self.node = DiscoveryNode(
            node_name="discovery1",
            ip="127.0.0.1",
            port=9100,
            testing=True
        )
        print("[Setup] DiscoveryNode creado para testing")

    def test_query_existing_node(self):
        # Registrar un nodo manualmente
        node = ServiceRegister("node1", "192.168.1.10", NodeType.ROUTING)
        self.node.register_table.add_node(node)

        # Crear mensaje de consulta
        msg = Message(
            type="DISCOVERY_QUERY_BY_NAME",
            src="192.168.1.100",
            dst=self.node.ip,
            payload={"name": "node1"}
        )

        response = self.node._on_message(msg, None)

        # Verificar que el nodo se devuelve correctamente en payload
        self.assertIsNotNone(response)
        self.assertIn("node", response.payload)
        returned_node = response.payload["node"]
        print(f"[Test] Nodo retornado: {returned_node}")

        self.assertEqual(returned_node["name"], "node1")
        self.assertEqual(returned_node["ip"], "192.168.1.10")
        self.assertEqual(returned_node["type"], NodeType.ROUTING.value)
        print("[Test] test_query_existing_node completado correctamente")

    def test_query_nonexistent_node(self):
        # Consultar un nodo que no existe
        msg = Message(
            type="DISCOVERY_QUERY_BY_NAME",
            src="192.168.1.101",
            dst=self.node.ip,
            payload={"name": "unknown_node"}
        )

        response = self.node._on_message(msg, None)

        # Debe retornar un payload con status error
        self.assertIsNotNone(response)
        self.assertEqual(response.payload.get("status"), "ERROR")
        self.assertIn("error_msg", response.payload)
        print(f"[Test] Respuesta para nodo desconocido: {response.payload}")
        print("[Test] test_query_nonexistent_node completado correctamente")

if __name__ == "__main__":
    print("[Main] Iniciando tests de DiscoveryNode query_by_name...")
    unittest.main()
    print("[Main] Todos los tests completados")
