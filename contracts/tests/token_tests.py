import unittest

from contracting.client import ContractingClient

class TokenTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        
        with open('../dai_token.py') as file:
            code = file.read()
        client.submit(code, name='dai_contract')

    def tearDown(self):
        self.client.flush()

    def test(self):
        pass
    
if __name__ == "__main__":
    unittest.main()
