import unittest
from comm import CommunicationNode
from comm import Message

class TestCommunicationNode(unittest.TestCase):

    def setUp(self):
        """Crea un nodo de comunicación con un handler de eco antes de cada test."""
        self.node = CommunicationNode(node_name="node1", ip="127.0.0.1", port=9001)

        # Handler de eco
        def echo_handler(msg, sock):
            """Devuelve el mismo payload recibido con tipo 'ECHO_RESPONSE'."""
            return Message(type="ECHO_RESPONSE", src=self.node.node_name, dst=msg.header["src"], payload=msg.payload)
        
        self.node.register_handler("ECHO", echo_handler)
        self.node.start_server()

    def tearDown(self):
        print("Deteniendo servidor....[TearDown]")
        """Detiene el nodo de comunicación después de cada test."""
        self.node.stop_server()

    def test_echo_message(self):
        """Verifica que el nodo puede recibir un mensaje 'ECHO' y responder correctamente con el mismo payload."""
        msg = Message(type="ECHO", src="client", dst="node1", payload={"text": "hello"})
        response = self.node.send_message("127.0.0.1", 9001, msg, await_response=True)
        self.assertIsNotNone(response)
        self.assertEqual(response.header["type"], "ECHO_RESPONSE")
        self.assertEqual(response.payload["text"], "hello")

if __name__ == "__main__":
    unittest.main()
