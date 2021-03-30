import unittest

from contracting.client import ContractingClient


class AuctionTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('dai_token.py') as file:
            dai = file.read()
        with open('basic_vault.py') as file:
            vault = file.read()
        with open('currency.py') as file:
            currency = file.read()
        with open('oracle.py') as file:
            oracle = file.read()
        self.client.submit(dai, name='dai_contract', constructor_args={
                           'vk': 'me', 'owner': 'default_owner'})
        self.client.submit(vault, name='vault_contract')
        self.client.submit(currency, name='currency')
        self.client.submit(oracle, name='oracle')
        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')
        self.currency = self.client.get_contract("currency")
        self.oracle = self.client.get_contract("oracle")

    def tearDown(self):
        self.client.flush()

    def test(self):
        pass


if __name__ == "__main__":
    unittest.main()
