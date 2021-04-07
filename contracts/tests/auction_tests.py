import unittest

from contracting.client import ContractingClient


class AuctionTests(unittest.TestCase):
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

        self.client.submit(dai, name='dai_contract', constructor_args={
                           'owner': 'vault_contract'})

        self.client.submit(vault, name='vault_contract')
        self.client.submit(currency, name='currency')
        self.client.submit(oracle, name='oracle')

        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')
        self.currency = self.client.get_contract('currency')
        self.oracle = self.client.get_contract('oracle')

    def tearDown(self):
        self.client.flush()

    def test_auction_vault_closed(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)
        with self.assertRaisesRegex(AssertionError, 'closed'):
            self.vault.open_force_close_auction(cdp_number=id)

    def test_auction_vault_in_auction(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=id)
        with self.assertRaisesRegex(AssertionError, 'already'):
            self.vault.open_force_close_auction(cdp_number=id)

if __name__ == '__main__':
    unittest.main()
