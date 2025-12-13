import unittest
from comm import Message, TCPServer, TCPClient

class TestTCP(unittest.TestCase):

    def setUp(self):
        """Configura un servidor TCP mock en un hilo antes de cada test."""
        self.ip = "127.0.0.1"
        self.port = 9000

        # Handler que responde siempre con un mensaje de confirmación
        def handler(msg, sock):
            return Message(type="RESPONSE", src="server", dst=msg.header["src"], payload={"ok": True})

        self.server = TCPServer(self.ip, self.port, handler)
        self.server.start()

    def tearDown(self):
        """Detiene el servidor TCP después de cada test."""
        self.server.stop()

    def test_send_receive(self):
        """Verifica que TCPClient puede enviar un mensaje y recibir la respuesta del servidor."""
        client = TCPClient()
        msg = Message(type="TEST", src="client1", dst="server", payload={"data": 123})
        response = client.send_message(self.ip, self.port, msg, await_response=True)
        self.assertIsNotNone(response)
        self.assertEqual(response.header["type"], "RESPONSE")
        self.assertEqual(response.payload["ok"], True)

if __name__ == "__main__":
    unittest.main()
