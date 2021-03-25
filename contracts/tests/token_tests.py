import unittest

from contracting.client import ContractingClient

client = ContractingClient()

with open('../dai_token.py') as file:
    code = file.read()
    client.submit(code, name='dai_token')

class TokenTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test(self):
        pass
    
if __name__ == "__main__":
    unittest.main()
