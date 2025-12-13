import unittest
from comm import Message

class TestMessage(unittest.TestCase):

    def test_serialization(self):
        """Verifica que un Message se serializa correctamente a un string JSON terminado en '\n'."""
        msg = Message(type="TEST", src="node1", dst="node2", payload={"key": "value"})
        json_str = msg.to_json()
        self.assertIsInstance(json_str, str)
        self.assertTrue(json_str.endswith("\n"))

    def test_deserialization(self):
        """Verifica que un Message serializado pueda ser deserializado a un objeto idéntico."""
        payload = {"key": "value"}
        msg = Message(type="TEST", src="node1", dst="node2", payload=payload)
        json_str = msg.to_json()
        msg2 = Message.from_json(json_str)
        self.assertEqual(msg.header["type"], msg2.header["type"])
        self.assertEqual(msg.header["src"], msg2.header["src"])
        self.assertEqual(msg.header["dst"], msg2.header["dst"])
        self.assertEqual(msg.payload, msg2.payload)
        self.assertEqual(msg.metadata["msg_id"], msg2.metadata["msg_id"])

if __name__ == "__main__":
    unittest.main()
