import unittest
from comm import CommunicationNode, Message
import time

class TestIntegrationCommunicationNodes(unittest.TestCase):

    def setUp(self):
        """Crea dos nodos de comunicación en puertos distintos con handlers de eco."""
        # Nodo 1
        self.node1 = CommunicationNode(node_name="node1", ip="127.0.0.1", port=9100)
        def handler_node1(msg, sock):
            """Responde con un mensaje indicando que lo recibió."""
            return Message(type="NODE1_RESPONSE", src="node1", dst=msg.header["src"], payload={"received": msg.payload})
        self.node1.register_handler("PING", handler_node1)
        self.node1.start_server()

        # Nodo 2
        self.node2 = CommunicationNode(node_name="node2", ip="127.0.0.1", port=9101)
        def handler_node2(msg, sock):
            """Responde con un mensaje indicando que lo recibió."""
            return Message(type="NODE2_RESPONSE", src="node2", dst=msg.header["src"], payload={"received": msg.payload})
        self.node2.register_handler("PING", handler_node2)
        self.node2.start_server()

        # Espera pequeña para asegurar que ambos servidores estén listos
        time.sleep(0.1)

    def tearDown(self):
        """Detiene ambos nodos después de cada test."""
        print("Deteniendo nodos....[TearDown]")
        self.node1.stop_server()
        self.node2.stop_server()
        time.sleep(0.05)

    def test_nodes_ping_pong(self):
        """Verifica que Node1 y Node2 puedan enviarse mensajes y recibir respuestas correctamente."""

        # Node1 envía mensaje a Node2
        msg1 = Message(type="PING", src="node1", dst="node2", payload={"msg": "hello from node1"})

        print("[Test] Node1 enviando PING a Node2")
        response1 = self.node1.send_message("127.0.0.1", 9101, msg1, await_response=True)
        print("[Test] Node1 recibió respuesta")

        self.assertIsNotNone(response1)
        self.assertEqual(response1.header["type"], "NODE2_RESPONSE")
        self.assertEqual(response1.payload["received"]["msg"], "hello from node1")

        # Node2 envía mensaje a Node1
        msg2 = Message(type="PING", src="node2", dst="node1", payload={"msg": "hello from node2"})
        
        print("[Test] Node2 enviando PING a Node1")
        response2 = self.node1.send_message("127.0.0.1", 9100, msg2, await_response=True)
        print("[Test] Node2 recibió respuesta")
        
        self.assertIsNotNone(response2)
        self.assertEqual(response2.header["type"], "NODE1_RESPONSE")
        self.assertEqual(response2.payload["received"]["msg"], "hello from node2")


if __name__ == "__main__":
    unittest.main()
