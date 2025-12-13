import unittest
import os
import time
from app.discovery import DiscoveryNode, ServiceRegister, NodeType
from comm import Message

class TestDiscoveryNodeCleanup(unittest.TestCase):

    def setUp(self):
        os.environ["DISCOVERY_SUBNET"] = "192.168.1.0/24"

        self.node = DiscoveryNode(
            node_name="discovery1",
            ip="127.0.0.1",
            port=9102,           # puerto diferente a otros tests
            heartbeat_timeout=3, # fácil de testear
            clean_interval=1,
            testing=True
        )
        print("[Setup] DiscoveryNode creado para test de limpieza")

        # Registrar nodos manualmente
        self.node.register_table.add_node(ServiceRegister("nodeA", "192.168.1.10", NodeType.ROUTING))
        self.node.register_table.add_node(ServiceRegister("nodeB", "192.168.1.11", NodeType.DATA))

        print("[Setup] Nodos A y B registrados")

    def test_cleanup_removes_dead_nodes(self):
        print("[Test] Iniciando test de limpieza de nodos...")

        # Enviar heartbeats a ambos nodos durante 3s
        start = time.time()
        while time.time() - start < 3:
            hbA = Message("DISCOVERY_HEARTBEAT", src="nodeA", dst=self.node.node_name, payload={"name": "nodeA"})
            hbB = Message("DISCOVERY_HEARTBEAT", src="nodeB", dst=self.node.node_name, payload={"name": "nodeB"})
            self.node._on_message(hbA, None)
            self.node._on_message(hbB, None)
            time.sleep(0.4)

        print("[Info] Ambos nodos activos antes de timeout")

        # Luego solo nodeA sigue enviando heartbeats → nodeB debe morir
        start = time.time()
        while time.time() - start < 4:
            hbA = Message("DISCOVERY_HEARTBEAT", src="nodeA", dst=self.node.node_name, payload={"name": "nodeA"})
            self.node._on_message(hbA, None)
            time.sleep(0.5)

        print("[Info] Tiempo de espera completado, nodeB debería expirar")

        # Leer nodos actuales
        alive = {n.name for n in self.node.register_table.get_all_nodes()}
        print(f"[Info] Nodos vivos después de limpieza: {alive}")

        self.assertIn("nodeA", alive)
        self.assertNotIn("nodeB", alive)

        print("[Test] test_cleanup_removes_dead_nodes completado correctamente")


if __name__ == "__main__":
    print("[Main] Iniciando tests de DiscoveryNode cleanup...")
    unittest.main()
    print("[Main] Todos los tests completados")
