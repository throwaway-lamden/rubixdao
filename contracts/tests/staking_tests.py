import datetime
import time
import unittest

from contracting.client import ContractingClient


class StakingTests(unittest.TestCase):
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
        with open('stake.py') as file:
            staking = file.read()

        self.client.submit(dai, name='dai_contract', constructor_args={
                           'owner': 'default_owner'})
        self.client.submit(vault, name='vault_contract')
        self.client.submit(currency, name='currency')
        self.client.submit(oracle, name='oracle')
        self.client.submit(staking, name='staking')

        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')
        self.currency = self.client.get_contract('currency')
        self.oracle = self.client.get_contract('oracle')
        self.staking = self.client.get_contract('staking')
        self.dai.mint(amount=2000000, signer='default_owner')

    def tearDown(self):
        self.client.flush()

    def test_metadata_unauthorised(self):
        with self.assertRaisesRegex(AssertionError, 'operator'):
            self.staking.change_metadata(
                key='testing', value='testing', signer='me')

    def test_metadata_normal(self):
        self.staking.change_metadata(key='testing', value='testing')
        assert self.staking.metadata['testing'] == 'testing'
        self.staking.change_metadata(key='testing', value='again')
        assert self.staking.metadata['testing'] == 'again'

    def test_change_owner_unauthorised(self):
        with self.assertRaisesRegex(AssertionError, 'operator'):
            self.staking.change_owner(new_owner='wallet2', signer='wallet2')

    def test_change_owner_normal(self):
        self.staking.change_owner(new_owner='wallet2')
        with self.assertRaisesRegex(AssertionError, 'operator'):
            self.staking.change_owner(new_owner='me')

    def test_change_rate_unauthorised(self):
        with self.assertRaisesRegex(AssertionError, 'operator'):
            self.staking.change_rate(new_rate=0.1, signer='wallet2')

    def test_change_rate_negative(self):
        with self.assertRaisesRegex(AssertionError, 'negative'):
            self.staking.change_rate(new_rate=-0.1)

    def test_change_rate_normal(self):
        current_price = self.staking.get_price()
        self.staking.change_rate(new_rate=0.1)

        self.assertAlmostEqual(1 + 0.1 / 31540000, self.staking.rate['rate'])
        self.assertAlmostEqual(self.staking.rate['start_price'], current_price)

    def test_stake_negative(self):
        with self.assertRaisesRegex(AssertionError, 'positive'):
            self.staking.stake(amount=-1)

    def test_stake_insufficient(self):
        with self.assertRaisesRegex(AssertionError, 'exceeds'):
            self.staking.stake(amount=1000001)

    def test_stake_normal(self):
        self.staking.stake(amount=1000000, signer='default_owner')

    def test_stake_updates_balance(self):
        self.staking.stake(amount=1000000, signer='default_owner')
        self.assertAlmostEqual(self.staking.balances['default_owner'], 1000000)

    def test_stake_sets_total_minted(self):
        self.staking.stake(amount=1000000, signer='default_owner')
        self.staking.stake(amount=1000000, signer='default_owner')
        self.assertAlmostEqual(self.staking.total_minted.get(), 2000000)

    def test_withdraw_stake_negative(self):
        self.staking.stake(amount=1000000, signer='default_owner')
        with self.assertRaisesRegex(AssertionError, 'positive'):
            self.staking.withdraw_stake(amount=-1, signer='default_owner')

    def test_withdraw_stake_insufficient(self):
        self.staking.stake(amount=1000000, signer='default_owner')
        with self.assertRaisesRegex(AssertionError, 'enough'):
            self.staking.withdraw_stake(amount=1000001, signer='default_owner')

    def withdraw_stake_normal(self):
        self.staking.stake(amount=1000000, signer='default_owner')
        self.staking.withdraw_stake(amount=1000000, signer='default_owner')

    def withdraw_stake_rewards(self):
        self.staking.stake(amount=1000000, signer='default_owner')
        self.staking.withdraw_stake(amount=1000000, signer='default_owner')
        self.assertAlmostEqual(self.dai.balance_of(account='default_owner'), 1000000)

    def test_get_price(self):
        current_rate = self.staking.rate['rate']
        time.sleep(4)
        with self.assertRaisesRegex(AssertionError, '!='):
            self.assertEqual(current_rate, self.staking.get_price())

    def test_timestamp(self):
        assert abs(datetime.datetime.utcnow().timestamp() -
                   self.staking.get_timestamp()) < 120


if __name__ == '__main__':
    unittest.main()
