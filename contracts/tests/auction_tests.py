import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime


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

        # Allow the vaults to be liquidated
        self.vault.vaults['currency', 'minimum_collateralization'] = 1.5
        self.oracle.set_price(number=0, new_price=0.01)

        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='stu', amount=1000, signer='vault_contract')
        self.dai.approve(to='vault_contract', amount=1000, signer='stu')

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

    def test_force_close_vault_default_bid(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        assert self.vault.cdp[self.id, 'auction', 'highest_bidder'] == 'sys'
        self.assertAlmostEqual(
            self.vault.cdp[self.id, 'auction', 'top_bid'], 0)

        assert self.vault.cdp[self.id, 'auction',
                              'time'] == self.vault.get_timestamp()

    def test_force_close_vault_default_bid_cannot_close(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        assert self.vault.cdp[self.id, 'auction', 'highest_bidder'] == 'sys'
        self.assertAlmostEqual(
            self.vault.cdp[self.id, 'auction', 'top_bid'], 0)

        assert self.vault.cdp[self.id, 'auction',
                              'time'] == self.vault.get_timestamp()

        with self.assertRaises(BaseException):
            env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
            self.vault.settle_force_close(
                cdp_number=self.id, environment=env)

    def test_force_close_vault_sufficent_collateral_fail(self):
        # self.vault.open_force_close_auction(cdp_number=self.id)
        pass

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

    def test_bid_on_force_close_normal(self):
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

    # recommend not breaking up because setup is long
    def test_multiple_user_bids(self):
        self.dai.transfer(to='wallet2', amount=50)
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        assert self.vault.cdp[self.id, 'auction', 'highest_bidder'] == 'sys'
        assert self.vault.cdp[self.id, 'auction', 'top_bid'] == 1
        assert self.vault.cdp[self.id, 'auction', 'sys', 'bid'] == 1

        with self.assertRaisesRegex(AssertionError, 'higher'):
            self.dai.approve(to='vault_contract', amount=1, signer='wallet2')
            self.vault.bid_on_force_close(
                cdp_number=self.id, amount=1, signer='wallet2')

        self.dai.approve(to='vault_contract', amount=2, signer='wallet2')

        self.vault.bid_on_force_close(
            cdp_number=self.id, amount=2, signer='wallet2')

        assert self.vault.cdp[self.id, 'auction',
                              'highest_bidder'] == 'wallet2'
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

    def test_settle_force_close_auction_open(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        with self.assertRaisesRegex(AssertionError, 'still'):
            self.vault.settle_force_close(cdp_number=self.id)

    def test_settle_force_close_auction_normal(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.vault.settle_force_close(cdp_number=self.id, environment=env)

    def test_settle_force_close_auction_state(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        highest_bidder, top_bid = self.vault.settle_force_close(
            cdp_number=self.id, environment=env)

        assert self.vault.cdp[self.id, 'auction', 'settled'] == True
        assert self.vault.cdp[self.id, 'open'] == False
        assert self.vault.cdp[self.id, 'auction', 'open'] == False
        assert self.vault.cdp[self.id, 'auction', self.vault.cdp[self.id,
                                                                 'auction', 'highest_bidder'], 'bid'] == 0
        assert highest_bidder == 'sys'
        assert top_bid == 1

    def test_settle_force_close_auction_burns_dai(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        original = self.dai.total_supply.get()
        self.vault.settle_force_close(cdp_number=self.id, environment=env)

        self.assertAlmostEqual(self.dai.total_supply.get(), original - 0.9)

    def test_settle_force_close_auction_returns_collateral(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        original = self.currency.balance_of(account='sys')
        self.vault.settle_force_close(cdp_number=self.id, environment=env)

        self.assertAlmostEqual(self.currency.balance_of(
            account='sys'), original + 1500)

    def test_settle_force_close_auction_updates_pool(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        with self.assertRaisesRegex(AttributeError, 'has'):
            stability = self.vault.stability_pool[self.vault.cdp[self.id,
                                                                 'vault_type']] # ?

        issued = self.vault.vaults[self.vault.cdp[self.id,
                                                  'vault_type'], 'issued']
        total = self.vault.vaults[self.vault.cdp[self.id,
                                                 'vault_type'], 'total']

        self.vault.settle_force_close(cdp_number=self.id, environment=env)

        self.assertAlmostEqual(
            self.vault.stability_pool[self.vault.cdp[self.id, 'vault_type']], 0.1)
        self.assertAlmostEqual(
            issued - 100, self.vault.vaults[self.vault.cdp[self.id, 'vault_type'], 'issued'])
        self.assertAlmostEqual(
            total - 0.9, self.vault.vaults[self.vault.cdp[self.id, 'vault_type'], 'total'])

    def test_claim_unwon_bid(self):
        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.claim_unwon_bid(cdp_number=1)

    def test_claim_unwon_bid_auction_open(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        with self.assertRaisesRegex(AssertionError, 'still'):
            self.vault.claim_unwon_bid(cdp_number=self.id)

    def test_claim_unwon_bid_nothing_left(self):
        self.vault.open_force_close_auction(cdp_number=self.id)

        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.vault.settle_force_close(cdp_number=self.id, environment=env)

        with self.assertRaisesRegex(AssertionError, 'negative'):
            self.vault.claim_unwon_bid(cdp_number=self.id)

    # recommend not breaking up because setup is long
    def test_claim_unwon_bid_normal(self):
        self.dai.transfer(to='wallet2', amount=50)

        self.vault.open_force_close_auction(cdp_number=self.id)

        self.dai.approve(to='vault_contract', amount=1)

        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)

        self.dai.approve(to='vault_contract', amount=2, signer='wallet2')

        self.vault.bid_on_force_close(
            cdp_number=self.id, amount=2, signer='wallet2')
        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.vault.settle_force_close(cdp_number=self.id, environment=env)

        self.assertAlmostEqual(self.dai.balance_of(account='sys'), 49)

        self.vault.claim_unwon_bid(cdp_number=self.id)

        self.assertAlmostEqual(self.dai.balance_of(account='sys'), 50)
        assert self.vault.cdp[self.id, 'auction', 'sys', 'bid'] == 0 #

    def test_instant_force_close_vault_sufficent_collateral_fail(self):
        # self.vault.open_force_close_auction(cdp_number=self.id)
        pass

    def test_instant_force_close_vault_normal(self):
        self.dai.approve(to='vault_contract', amount=1000)

        self.vault.fast_force_close_vault(cdp_number=self.id)

    def test_instant_force_close_nonexistent(self):
        self.dai.approve(to='vault_contract', amount=1000)

        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.fast_force_close_vault(cdp_number=1)

    def test_instant_force_close_cannot_close_twice(self):
        self.dai.approve(to='vault_contract', amount=1000)

        self.vault.fast_force_close_vault(cdp_number=self.id)

        with self.assertRaisesRegex(AssertionError, 'already'):
            self.dai.approve(to='vault_contract', amount=1000)

            self.vault.fast_force_close_vault(cdp_number=self.id)

    def test_after_instant_force_close_cannot_open_auction(self):
        self.dai.approve(to='vault_contract', amount=1000)
        self.vault.fast_force_close_vault(cdp_number=self.id)

        with self.assertRaisesRegex(AssertionError, 'already'):
            self.vault.open_force_close_auction(cdp_number=self.id)

    def test_instant_force_close_takes_dai_when_ratio_is_above_1_03(self):
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')

        self.oracle.set_price(number=0, new_price=0.09)

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance = self.dai.balances['sys']

        self.vault.fast_force_close_vault(cdp_number=self.id)
        assert self.dai.balance_of(account='sys') < old_balance

    def test_instant_force_close_takes_correct_amount_of_dai_when_ratio_is_above_1_03(self):
        self.oracle.set_price(number=0, new_price=0.09)
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance = self.dai.balances['sys']

        self.vault.fast_force_close_vault(cdp_number=self.id)
        assert self.dai.balance_of(account='sys') == old_balance - (100 * 1.1)

    def test_instant_force_close_gives_collateral_when_ratio_is_above_1_03(self):
        self.oracle.set_price(number=0, new_price=0.09)
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')

        self.dai.approve(to='vault_contract', amount=1000, signer='stu')
        old_balance = old_balance = self.currency.balance_of(account='stu')

        self.vault.fast_force_close_vault(cdp_number=self.id, signer='stu')
        assert self.currency.balance_of(account='stu') > old_balance

    def test_instant_force_close_gives_correct_proportion_of_collateral_when_ratio_is_above_1_03(self):
        self.oracle.set_price(number=0, new_price=0.09)

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance_dai = self.dai.balances['stu']
        old_balance_collateral = old_balance = self.currency.balance_of(account='stu')

        self.vault.fast_force_close_vault(cdp_number=self.id, signer='stu')

        # The math in this might not be right - if it fails, check it!
        self.assertAlmostEqual(float((self.currency.balance_of(account='stu') - old_balance_collateral)) / 1.03 * 0.09, old_balance_dai - self.dai.balance_of(account='stu'))

    def test_instant_force_close_returns_collateral_to_owner_when_ratio_is_above_1_03(self):
        self.oracle.set_price(number=0, new_price=0.09)

        self.dai.approve(to='vault_contract', amount=1000, signer='stu')
        old_balance = self.currency.balance_of(account='sys')

        self.vault.fast_force_close_vault(cdp_number=self.id, signer='stu')
        assert self.currency.balance_of(account='sys') > old_balance

    def test_instant_force_close_returns_correct_amount_of_collateral_to_owner_when_ratio_is_above_1_03(self):
        self.oracle.set_price(number=0, new_price=0.09)

        self.dai.approve(to='vault_contract', amount=1000, signer='stu')
        old_balance = self.currency.balance_of(account='sys')

        self.vault.fast_force_close_vault(cdp_number=self.id, signer='stu')
        self.assertAlmostEqual(self.currency.balance_of(account='sys'), old_balance + 1500 - (110 * 1.03) / 0.09)

    def test_instant_force_close_gives_correct_amount_of_collateral_when_ratio_is_above_1_03(self):
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')
        self.oracle.set_price(number=0, new_price=0.09)

        self.dai.approve(to='vault_contract', amount=1000, signer='stu')
        old_balance = self.currency.balance_of(account='stu')

        self.dai.approve(to='vault_contract', amount=1000)
        self.vault.fast_force_close_vault(cdp_number=self.id)
        assert self.currency.balance_of(account='stu') == (old_balance + 1500)

    def test_instant_force_close_takes_into_account_stability_fee_when_ratio_is_above_1_03(self): # TODO: make this less complex
        self.oracle.set_price(number=0, new_price=1.0)
        self.currency.approve(to='vault_contract', amount=1500)
        v_id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.oracle.set_price(number=0, new_price=0.01)

        self.dai.approve(to='vault_contract', amount=1000, signer='stu')
        self.vault.fast_force_close_vault(cdp_number=v_id, signer='stu')

        assert self.vault.vaults[0, 'issued'] == 200 - 100

        # redemption_cost = 100 * 1.1 # don't know why this is here
        amount_redeemed = 15 / 1.03
        self.assertAlmostEqual(self.vault.vaults[0, 'total'], 200 - (amount_redeemed / 1.1))

        self.oracle.set_price(number=0, new_price=0.15) # This is a inconsistent price because otherwise the ratio drops below 1.03

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance = old_balance = self.currency.balance_of(account='stu')

        self.vault.fast_force_close_vault(cdp_number=self.id, signer='stu')

        # May not work if the ratio becomes less than 1.03 - double check
        assert self.dai.balance_of(account='stu') == 1000 - amount_redeemed - (self.vault.vaults[0, 'total'] / self.vault.vaults[0, 'issued']) * 110
        assert self.currency.balance_of(account='stu') == old_balance + (((self.vault.vaults[0, 'total'] / self.vault.vaults[0, 'issued']) * 110 * 1.03) / 0.15)

    def test_instant_force_close_does_not_update_stability_fee_when_ratio_is_above_1_03(self):
        self.oracle.set_price(number=0, new_price=0.09)
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')

        self.dai.approve(to='vault_contract', amount=1000)
        self.vault.fast_force_close_vault(cdp_number=self.id)

        assert self.vault.vaults[0, 'issued'] == 0
        assert self.vault.vaults[0, 'total'] == 0

    def test_instant_force_close_takes_dai_when_ratio_is_below_1_03(self):
        pass
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance = self.dai.balances['sys']

        self.vault.fast_force_close_vault(cdp_number=self.id)
        assert self.dai.balance_of(account='sys') < old_balance

    def test_instant_force_close_takes_correct_amount_of_dai_when_ratio_is_below_1_03(self):
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance = [self.dai.balances['sys'], self.currency.balances['sys']]

        self.vault.fast_force_close_vault(cdp_number=self.id)

        self.assertAlmostEqual(self.dai.balance_of(account='sys'), old_balance[0] - 15 / (1.03))
        self.assertAlmostEqual(self.currency.balance_of(account='sys'), old_balance[1] + 1500)

    def test_instant_force_close_gives_collateral_when_ratio_is_below_1_03(self):
        pass
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')
        self.oracle.set_price(number=0, new_price=0.09)

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance = self.currency.balance_of(account='sys')

        self.vault.fast_force_close_vault(cdp_number=self.id)
        assert self.currency.balance_of(account='sys') > old_balance

    def test_instant_force_close_gives_correct_proportion_of_collateral_when_ratio_is_below_1_03(self):
        pass

        self.oracle.set_price(number=0, new_price=0.01)

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance_dai = self.dai.balances['sys']
        old_balance_collateral = self.currency.balances['sys']

        self.vault.fast_force_close_vault(cdp_number=self.id)

        # The math in this might not be right - if it fails, check it!
        self.assertAlmostEqual((self.currency.balance_of(account='sys') - old_balance_collateral) / 1.03 * 0.01, old_balance_dai - self.dai.balance_of(account='sys'))

    def test_instant_force_close_gives_correct_amount_of_collateral_when_ratio_is_below_1_03(self):
        pass
        self.dai.mint(amount=1000, signer='vault_contract')
        self.dai.transfer(to='sys', amount=1000, signer='vault_contract')

        self.oracle.set_price(number=0, new_price=0.09)

        self.dai.approve(to='vault_contract', amount=1000)
        old_balance = self.currency.balance_of(account='sys')

        self.vault.fast_force_close_vault(cdp_number=self.id)
        assert self.currency.balance_of(account='sys') == old_balance + 1500

if __name__ == '__main__':
    unittest.main()
