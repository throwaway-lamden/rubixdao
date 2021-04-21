import unittest

from contracting.client import ContractingClient


class BuySellTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()

        with open('dai.py') as file:
            dai = file.read()

        with open('vault.py') as file:
            vault = file.read()

        with open('test_currency.py') as file:
            currency = file.read()

        with open('oracle.py') as file:
            oracle = file.read()

        with open('test_amm.py') as file:
            amm = file.read()

        with open('../keeper-examples/buy_and_sell.py') as file:
            buysell = file.read()

        self.client.submit(dai, name='dai_contract', constructor_args={
                           'owner': 'vault_contract'})
        self.client.submit(vault, name='vault_contract')
        self.client.submit(currency, name='currency')
        self.client.submit(oracle, name='oracle')
        self.client.submit(amm, name='amm')
        self.client.submit(buysell, name='buysell')

        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')
        self.currency = self.client.get_contract('currency')
        self.oracle = self.client.get_contract('oracle')
        self.amm = self.client.get_contract('amm')
        self.buysell = self.client.get_contract('buysell')

    def tearDown(self):
        self.client.flush()

    def test_buysell_main(self):
        self.buysell.main()

if __name__ == '__main__':
    unittest.main()
