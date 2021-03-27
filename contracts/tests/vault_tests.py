import unittest

from contracting.client import ContractingClient


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('dai_token.py') as file:
            code = file.read()
        self.client.submit(code, name='dai_token', constructor_args={
                           'vk': 'me', 'owner': 'default_owner'})
        self.token = self.client.get_contract('dai_token')
        with open('basic_vault.py') as file:
            code = file.read()
        self.client.submit(code, name='basic_vault')
        self.vault = self.client.get_contract('basic_vault')

    def tearDown(self):
        self.client.flush()

    def test(self):
        pass


if __name__ == "__main__":
    unittest.main()
