import unittest
import os
from app.discovery import DiscoveryNode, ServiceRegister, NodeType
from comm import Message

class TestDiscoveryNodeQueryByType(unittest.TestCase):

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
        node1 = ServiceRegister("node1", "192.168.1.10", NodeType.ROUTING)
        node2 = ServiceRegister("node2", "192.168.1.11", NodeType.ROUTING)
        node3 = ServiceRegister("node3", "192.168.1.12", NodeType.DATA)

        self.node.register_table.add_node(node1)
        self.node.register_table.add_node(node2)
        self.node.register_table.add_node(node3)

        # Crear mensaje de consulta
        msg = Message(
            type="DISCOVERY_QUERY_BY_TYPE",
            src="192.168.1.100",
            dst=self.node.ip,
            payload={"type": "ROUTING"}
        )

        response = self.node._on_message(msg, None)

        # Verificar que el nodo se devuelve correctamente en payload
        self.assertIsNotNone(response)
        self.assertIn("nodes", response.payload)
        returned_nodes = response.payload["nodes"]
        print(f"[Test] Nodo retornado: {returned_nodes}")

        self.assertEqual(len(returned_nodes), 2)
        i = 1
        for rtn_node in returned_nodes:
            self.assertEqual(rtn_node["name"], "node" + str(i))
            self.assertEqual(rtn_node["ip"], "192.168.1.1" + str(i - 1))
            self.assertEqual(rtn_node["type"], NodeType.ROUTING.value)
            i += 1

        print("[Test] test_query_existing_node completado correctamente")

    def test_query_nonexistent_node(self):
        # Consultar un nodo que no existe
        msg = Message(
            type="DISCOVERY_QUERY_BY_TYPE",
            src="192.168.1.101",
            dst=self.node.ip,
            payload={"type": "UNKNOWN_TYPE"}
        )

        response = self.node._on_message(msg, None)

        # Debe retornar un payload con status error
        self.assertIsNotNone(response)
        self.assertEqual(response.payload.get("status"), "ERROR")
        self.assertIn("error_msg", response.payload)
        print(f"[Test] Respuesta para nodo desconocido: {response.payload}")
        print("[Test] test_query_nonexistent_node completado correctamente")

if __name__ == "__main__":
    print("[Main] Iniciando tests de DiscoveryNode query_by_type...")
    unittest.main()
    print("[Main] Todos los tests completados")