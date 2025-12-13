import unittest
import os
from app.discovery import DiscoveryNode, ServiceRegister, NodeType
from comm import Message

class TestDiscoveryNodeQueryAll(unittest.TestCase):

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

    def test_query_all_empty_table(self):
        # Consultar un nodo que no existe
        msg = Message(
            type="DISCOVERY_QUERY_ALL",
            src="192.168.1.101",
            dst=self.node.ip,
            payload={}
        )

        response = self.node._on_message(msg, None)

        # Debe retornar status OK con lista vacía.
        self.assertIsNotNone(response)
        self.assertEqual(response.payload.get("status"), "OK")
        
        self.assertIn("nodes", response.payload)
        returned_nodes = response.payload["nodes"]
        self.assertEqual(len(returned_nodes), 0)

        print(f"[Info] Lista retornada contiene {len(returned_nodes)} nodos.")
        print("[Test] test_query_all_empty_table completado correctamente")

    def test_query_all(self):
        # Registrar un nodo manualmente
        node1 = ServiceRegister("node1", "192.168.1.10", NodeType.ROUTING)
        node2 = ServiceRegister("node2", "192.168.1.11", NodeType.ROUTING)
        node3 = ServiceRegister("node3", "192.168.1.12", NodeType.DATA)
        node4 = ServiceRegister("node4", "192.168.1.13", NodeType.AUTH)

        self.node.register_table.add_node(node1)
        self.node.register_table.add_node(node2)
        self.node.register_table.add_node(node3)
        self.node.register_table.add_node(node4)

        # Crear mensaje de consulta
        msg = Message(
            type="DISCOVERY_QUERY_ALL",
            src="192.168.1.100",
            dst=self.node.ip,
            payload={}
        )

        response = self.node._on_message(msg, None)

        # Verificar que el nodo se devuelve correctamente en payload
        self.assertIsNotNone(response)
        self.assertIn("status", response.payload)
        self.assertEqual(response.payload["status"], "OK")

        self.assertIn("nodes", response.payload)
        returned_nodes = response.payload["nodes"]
        print(f"[Test] Nodos retornado: {returned_nodes}")

        self.assertEqual(len(returned_nodes), 4)
        i = 1
        for rtn_node in returned_nodes:
            self.assertEqual(rtn_node["name"], "node" + str(i))
            self.assertEqual(rtn_node["ip"], "192.168.1.1" + str(i - 1))
            i += 1

        print("[Test] test_query_all completado correctamente")

if __name__ == "__main__":
    print("[Main] Iniciando tests de DiscoveryNode query_all...")
    unittest.main()
    print("[Main] Todos los tests completados")