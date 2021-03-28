import unittest

from contracting.client import ContractingClient

client = ContractingClient()


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('dai_token.py') as file:
            dai = file.read()
        with open('basic_vault.py') as file:
            vault = file.read()
        self.client.submit(dai, name='dai_contract', constructor_args={
                           'vk': 'me', 'owner': 'default_owner'})
        self.client.submit(vault, name = 'vault_contract')
        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')

    def tearDown(self):
        self.client.flush()

    def test(self):
        pass
