import datetime
import time
import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime


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
                           'owner': 'vault_contract'})
        self.client.submit(vault, name='vault_contract')
        self.client.submit(currency, name='currency')
        self.client.submit(oracle, name='oracle')
        self.client.submit(staking, name='staking')

        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')
        self.currency = self.client.get_contract('currency')
        self.oracle = self.client.get_contract('oracle')
        self.staking = self.client.get_contract('staking')
        self.dai.mint(amount=2000000, signer='vault_contract')
        self.dai.transfer(amount=2000000, to='testing_user', signer='vault_contract')

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
        with self.assertRaisesRegex(AssertionError, 'enough'):
            self.staking.stake(amount=1000001)

    def test_stake_normal(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')

    def test_stake_takes_money(self):
        self.assertAlmostEqual(self.dai.balance_of(
            account='testing_user'), 2000000)
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.assertAlmostEqual(self.dai.balance_of(
            account='testing_user'), 1000000)

    def test_stake_updates_balance(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.assertAlmostEqual(self.staking.balances['testing_user'], 1000000)

    def test_stake_sets_total_minted(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.assertAlmostEqual(self.staking.total_minted.get(), 2000000)

    def test_withdraw_stake_negative(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        with self.assertRaisesRegex(AssertionError, 'positive'):
            self.staking.withdraw_stake(amount=-1, signer='testing_user')

    def test_withdraw_stake_insufficient(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        with self.assertRaisesRegex(AssertionError, 'enough'):
            self.staking.withdraw_stake(amount=1000001, signer='testing_user')

    def test_stake_records_balance(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.assertAlmostEqual(self.staking.balances['testing_user'], 1000000)
        self.assertEqual(self.staking.balances['wallet2'], None)

    def test_withdraw_stake_normal(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.withdraw_stake(amount=1000000, signer='testing_user')

    def test_withdraw_stake_returns_money(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.withdraw_stake(amount=1000000, signer='testing_user')
        self.assertAlmostEqual(self.dai.balance_of(
            account='testing_user'), 2000000)

    def test_withdraw_stake_returns_rewards(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.staking.withdraw_stake(
            amount=1000000, signer='testing_user', environment=env)
        with self.assertRaisesRegex(AssertionError, '!='):
            self.assertEqual(self.dai.balance_of(
                account='testing_user'), 2000000)

    def test_transfer_negative(self):
        with self.assertRaisesRegex(AssertionError, 'non-positive'):
            self.staking.transfer(amount=-1, to='wallet2', signer='testing_user')

    def test_transfer_excess(self):
        with self.assertRaisesRegex(AssertionError, 'enough'):
            self.staking.transfer(amount=1000001, to='wallet2', signer='testing_user')

    def test_transfer_normal(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.transfer(amount=42, to='wallet2', signer='testing_user')
        self.assertAlmostEqual(
            self.staking.balance_of(account='testing_user'), 1000000 - 42)
        self.assertAlmostEqual(self.staking.balance_of(account='wallet2'), 42)

    def test_accounts_negative(self):
        with self.assertRaisesRegex(AssertionError, 'non-positive'):
            self.staking.approve(amount=-1, to='account1', signer='testing_user')

    def test_accounts_excess(self):
        with self.assertRaisesRegex(AssertionError, 'exceeds'):
            self.staking.approve(amount=1000001, to='account1', signer='testing_user')

    def test_accounts_normal(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.approve(amount=42, to='account1', signer='testing_user')
        self.assertAlmostEqual(self.staking.allowance(
            owner='testing_user', spender='account1', signer='me'), 42)

    def test_transfer_from_negative(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.approve(amount=42, to='account1', signer='testing_user')
        with self.assertRaisesRegex(AssertionError, 'non-positive'):
            self.staking.transfer_from(amount=-1, to='wallet2',
                                   main_account='testing_user', signer='account1')

    def test_transfer_from_excess(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.approve(amount=42, to='account1', signer='testing_user')
        with self.assertRaisesRegex(AssertionError, 'enough'):
            self.staking.transfer_from(amount=1000001, to='wallet2',
                                   main_account='testing_user', signer='account1')

    def test_transfer_from_approved(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.approve(amount=42, to='account1', signer='testing_user')
        with self.assertRaisesRegex(AssertionError, 'approved'):
            self.staking.transfer_from(amount=1000001, to='wallet2',
                                   main_account='testing_user', signer='account1')

    def test_transfer_from_normal_sends(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.approve(amount=42, to='account1', signer='testing_user')
        self.staking.transfer_from(amount=42, to='wallet2',
                               main_account='testing_user', signer='account1')
        self.assertAlmostEqual(self.staking.allowance(
            owner='testing_user', spender='account1', signer='me'), 0)
        self.assertAlmostEqual(
            self.staking.balance_of(account='testing_user'), 1000000 - 42)

    def test_transfer_from_normal_receives(self):
        self.dai.approve(to='staking', amount=1000000, signer='testing_user')
        self.staking.stake(amount=1000000, signer='testing_user')
        self.staking.approve(amount=42, to='account1', signer='testing_user')
        self.staking.transfer_from(amount=42, to='wallet2',
                               main_account='testing_user', signer='account1')
        self.assertAlmostEqual(self.staking.balance_of(account='wallet2'), 42)

    def test_get_price(self):
        current_rate = self.staking.get_price()
        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        with self.assertRaisesRegex(AssertionError, '!='):
            self.assertEqual(current_rate, self.staking.get_price(
                environment=env))

    def test_timestamp(self):
        assert abs(datetime.datetime.utcnow().timestamp() -
                   self.staking.get_timestamp()) < 120


if __name__ == '__main__':
    unittest.main()
