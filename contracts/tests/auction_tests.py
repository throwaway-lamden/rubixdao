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

        self.oracle.set_price(number=0, new_price=1.0)
        self.currency.approve(to='vault_contract', amount=1500)
        self.id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)

    def tearDown(self):
        self.client.flush()

    def test_force_close_vault_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.open_force_close_auction(cdp_number=1)

    def test_force_close_vault_closed(self):
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=self.id)
        with self.assertRaisesRegex(AssertionError, 'closed'):
            self.vault.open_force_close_auction(cdp_number=self.id)

    def test_force_close_vault_in_auction(self):
        self.vault.open_force_close_auction(cdp_number=self.id)
        with self.assertRaisesRegex(AssertionError, 'already'):
            self.vault.open_force_close_auction(cdp_number=self.id)

    def test_force_close_vault_frozen(self):
        self.vault.open_force_close_auction(cdp_number=self.id)
        assert self.vault.cdp[self.id, 'open'] == False
        assert self.vault.cdp[self.id, 'auction', 'open'] == True

    def test_force_close_vault_top_bid(self):
        self.vault.open_force_close_auction(cdp_number=self.id)
        assert self.vault.cdp[self.id, 'auction', 'highest_bidder'] == 'sys'
        self.assertAlmostEqual(self.vault.cdp[self.id, 'auction', 'top_bid'], 0)
        assert self.vault.cdp[self.id, 'auction', 'time'] == self.vault.get_timestamp()

    def test_force_close_vault_normal(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

    def test_bid_on_force_close_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.bid_on_force_close(cdp_number=1, amount=1)

    def test_bid_on_force_close_no_auction(self):
        with self.assertRaisesRegex(AssertionError, 'Auction'):
            self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

    def test_bid_on_force_close_higher_bid(self):
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=2)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=2)
        with self.assertRaisesRegex(AssertionError, 'higher'):
            self.dai.approve(to='vault_contract', amount=1)
            self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

    def test_bid_on_force_close_takes_dai(self):
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=2)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=2)
        assert self.dai.balance_of(account='sys') == 98

    def test_bid_on_force_close_sets_bid(self):
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=2)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=2)
        assert self.vault.cdp[self.id, 'auction', 'highest_bidder'] == 'sys'
        assert self.vault.cdp[self.id, 'auction', 'top_bid'] == 2
        assert self.vault.cdp[self.id, 'auction', 'sys', 'bid'] == 2

    def test_bid_on_force_close_raise_bid(self):
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)
        assert self.dai.balance_of(account='sys') == 99
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=2)
        assert self.dai.balance_of(account='sys') == 98

    def test_multiple_user_bids(self):  # recommend not breaking up because setup is long
        self.dai.transfer(to='wallet2', amount=50)
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)
        assert self.vault.cdp[self.id, 'auction', 'highest_bidder'] == 'sys'
        assert self.vault.cdp[self.id, 'auction', 'top_bid'] == 1
        assert self.vault.cdp[self.id, 'auction', 'sys', 'bid'] == 1
        with self.assertRaisesRegex(AssertionError, 'higher'):
            self.dai.approve(to='vault_contract', amount=1, signer='wallet2')
            self.vault.bid_on_force_close(cdp_number=self.id, amount=1, signer='wallet2')
        self.dai.approve(to='vault_contract', amount=2, signer='wallet2')
        self.vault.bid_on_force_close(cdp_number=self.id, amount=2, signer='wallet2')
        assert self.vault.cdp[self.id, 'auction', 'highest_bidder'] == 'wallet2'
        assert self.vault.cdp[self.id, 'auction', 'top_bid'] == 2
        assert self.vault.cdp[self.id, 'auction', 'wallet2', 'bid'] == 2
        assert self.vault.cdp[self.id, 'auction', 'sys', 'bid'] == 1

    def test_settle_force_close_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.settle_force_close(cdp_number=1)

    def test_settle_force_close_no_auction(self):
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=self.id)
        with self.assertRaisesRegex(AssertionError, 'not'):
            self.vault.settle_force_close(cdp_number=self.id)

if __name__ == '__main__':
    unittest.main()
