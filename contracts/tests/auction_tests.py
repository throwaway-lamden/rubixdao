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

    def test_force_close_vault_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.open_force_close_auction(cdp_number=0)

    def test_force_close_vault_closed(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)
        with self.assertRaisesRegex(AssertionError, 'closed'):
            self.vault.open_force_close_auction(cdp_number=id)

    def test_force_close_vault_in_auction(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=id)
        with self.assertRaisesRegex(AssertionError, 'already'):
            self.vault.open_force_close_auction(cdp_number=id)

    def test_force_close_vault_frozen(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=id)
        assert self.vault.cdp[id, 'open'] == False
        assert self.vault.cdp[id, 'auction', 'open'] == True

    def test_force_close_vault_top_bid(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=id)
        assert self.vault.cdp[id, 'auction', 'highest_bidder'] == 'sys'
        self.assertAlmostEqual(self.vault.cdp[id, 'auction', 'top_bid'], 0)
        assert self.vault.cdp[id, 'auction', 'time'] == self.vault.get_timestamp()

    def test_force_close_vault_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=id)

    def test_bid_on_force_close_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.bid_on_force_close(cdp_number=0, amount=1)

    def test_bid_on_force_close_closed(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)
        with self.assertRaisesRegex(AssertionError, 'closed'):
            self.vault.bid_on_force_close(cdp_number=id, amount=1)

    def test_bid_on_force_close_no_auction(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        with self.assertRaisesRegex(AssertionError, 'open'):
            self.vault.bid_on_force_close(cdp_number=id, amount=1)

    def test_bid_on_force_close_higher_bid(self):
        pass

    def test_bid_on_force_close_takes_dai(self):
        pass

    def test_bid_on_force_close_updates_bid(self):
        pass

if __name__ == '__main__':
    unittest.main()
