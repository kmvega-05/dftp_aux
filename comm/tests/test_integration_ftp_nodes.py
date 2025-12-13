import unittest
import time
from comm import CommunicationNode, Message

class TestIntegrationFTPNodes(unittest.TestCase):

    def setUp(self):
        """Crea nodos simulados de routing, processing, data y auth con handlers de prueba."""
        # ---------------- Nodos ----------------
        self.routing_node = CommunicationNode(node_name="routing1", ip="127.0.0.1", port=9300)
        self.processing_node = CommunicationNode(node_name="processing1", ip="127.0.0.1", port=9301)
        self.data_node = CommunicationNode(node_name="data1", ip="127.0.0.1", port=9302)
        self.auth_node = CommunicationNode(node_name="auth1", ip="127.0.0.1", port=9303)

        # ---------------- Handlers ----------------
        # Routing node
        self.routing_node.register_handler("PROCESS_FTP_COMMAND", lambda msg, sock:
            Message(type="PROCESS_RESPONSE", src="routing1", dst=msg.header["src"], payload={"ack": True})
        )

        # Processing node
        self.processing_node.register_handler("PROCESS_FTP_COMMAND", lambda msg, sock:
            Message(type="PROCESS_RESPONSE", src="processing1", dst=msg.header["src"], payload={"cmd_executed": msg.payload["cmd"]})
        )
        self.processing_node.register_handler("AUTH_VALIDATE_USER", lambda msg, sock:
            Message(type="AUTH_RESPONSE", src="processing1", dst=msg.header["src"], payload={"valid": True})
        )
        self.processing_node.register_handler("DATA_READ", lambda msg, sock:
            Message(type="DATA_RESPONSE", src="processing1", dst=msg.header["src"], payload={"data": "dummy"})
        )

        # Data node
        self.data_node.register_handler("DATA_READ", lambda msg, sock:
            Message(type="DATA_RESPONSE", src="data1", dst=msg.header["src"], payload={"data": "dummy_file"})
        )

        # Auth node
        self.auth_node.register_handler("AUTH_VALIDATE_USER", lambda msg, sock:
            Message(type="AUTH_RESPONSE", src="auth1", dst=msg.header["src"], payload={"valid": True})
        )

        # ---------------- Inicia servidores ----------------
        self.routing_node.start_server()
        self.processing_node.start_server()
        self.data_node.start_server()
        self.auth_node.start_server()

        # Pequeña espera para asegurar que todos los servidores estén listos
        time.sleep(0.1)

    def tearDown(self):
        """Detiene todos los nodos."""
        print("Deteniendo nodos...[TearDown]")
        self.routing_node.stop_server()
        self.processing_node.stop_server()
        self.data_node.stop_server()
        self.auth_node.stop_server()
        time.sleep(0.05)

    def test_mock_ftp_message_flow(self):
        """Simula el flujo de mensajes FTP entre nodos y verifica respuestas."""

        # Routing node envía un comando FTP a processing
        cmd_msg = Message(type="PROCESS_FTP_COMMAND", src="routing1", dst="processing1", payload={"cmd": "LIST"})
        print("[Test] Routing envia PROCESS_FTP_COMMAND a Processing")
        response = self.routing_node.send_message("127.0.0.1", 9301, cmd_msg, await_response=True)
        self.assertIsNotNone(response)
        self.assertEqual(response.header["type"], "PROCESS_RESPONSE")
        self.assertEqual(response.payload["cmd_executed"], "LIST")
        print("[Test] Routing recibió respuesta de Processing")

        # Processing node valida usuario con Auth
        auth_msg = Message(type="AUTH_VALIDATE_USER", src="processing1", dst="auth1", payload={"user": "test"})
        print("[Test] Processing envia AUTH_VALIDATE_USER a Auth")
        response = self.processing_node.send_message("127.0.0.1", 9303, auth_msg, await_response=True)
        self.assertIsNotNone(response)
        self.assertEqual(response.header["type"], "AUTH_RESPONSE")
        self.assertTrue(response.payload["valid"])
        print("[Test] Processing recibió respuesta de Auth")

        # Processing node lee datos del Data node
        data_msg = Message(type="DATA_READ", src="processing1", dst="data1", payload={"file": "dummy.txt"})
        print("[Test] Processing envia DATA_READ a Data")
        response = self.processing_node.send_message("127.0.0.1", 9302, data_msg, await_response=True)
        self.assertIsNotNone(response)
        self.assertEqual(response.header["type"], "DATA_RESPONSE")
        self.assertEqual(response.payload["data"], "dummy_file")
        print("[Test] Processing recibió respuesta de Data")


if __name__ == "__main__":
    unittest.main()
