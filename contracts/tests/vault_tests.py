import datetime
import random
import time
import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime


class VaultTests(unittest.TestCase):
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
        self.vault.change_any_state(
            key=('mint', 'DSR', 'owner'), new_value='sys')
        self.vault.change_any_state(key=(0, 'DSR', 'owner'), new_value='sys')
        self.vault.change_any_state(
            key=('currency', 'DSR', 'owner'), new_value='sys')

    def tearDown(self):
        self.client.flush()

    def test_create_vault_unavailable(self):
        with self.assertRaisesRegex(AssertionError, 'available'):
            self.vault.create_vault(
                vault_type=-1, amount_of_dai=100, amount_of_collateral=100)

    def test_create_vault_negative(self):
        with self.assertRaisesRegex(AssertionError, 'positive'):
            self.vault.create_vault(vault_type=0, amount_of_dai=-
                                    1,  amount_of_collateral=100)

    def test_create_vault_insufficient_allowance(self):
        with self.assertRaisesRegex(AssertionError, 'allowance'):
            self.vault.create_vault(
                vault_type=0, amount_of_dai=1000001,
                amount_of_collateral=1000001)

    def test_create_vault_insufficient_collateral(self):
        self.currency.approve(to='vault_contract', amount=100)
        with self.assertRaisesRegex(AssertionError, 'collateral'):
            self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                    amount_of_collateral=100)

    def test_create_vault_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)

    def test_create_vault_states(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)

        assert self.vault.cdp['current_value'] == 1
        assert self.vault.cdp[id, 'owner'] == 'sys'
        assert self.vault.cdp[id, 'open'] == True
        assert self.vault.cdp[id,
                              'collateral_type'] == self.vault.vaults[0, 'collateral_type']
        assert self.vault.cdp[id, 'vault_type'] == 0
        assert self.vault.cdp[id, 'dai'] == 100
        assert self.vault.cdp[id, 'collateral_amount'] == 1500
        assert self.vault.cdp[id, 'time'] == self.vault.get_timestamp()

    def test_create_vault_takes_collateral(self):
        self.currency.transfer(to='stu', amount=1500)
        self.currency.approve(to='vault_contract', amount=1500, signer='stu')

        self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500,
            signer='stu')  # Might fail, not sure why commented

        self.assertEqual(self.currency.balances['stu'], 0)

    def test_create_vault_gives_dai(self):
        self.currency.transfer(to='stu', amount=1500)
        self.currency.approve(to='vault_contract', amount=1500, signer='stu')

        self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500,
            signer='stu')  # Might fail, not sure why commented

        self.assertEqual(self.dai.balances['stu'], 100)

    def test_create_vault_updates_reserves(self):
        self.currency.approve(to='vault_contract', amount=1500)

        self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500)

        self.assertEqual(self.vault.vaults[0, 'issued'], 100)
        self.assertEqual(self.vault.vaults[0, 'total'], 100)

    def test_any_state_unauthorised(self):
        with self.assertRaisesRegex(AssertionError, 'owner'):
            self.vault.change_any_state(
                key='testing', new_value='testing', signer='me')

    def test_any_state_normal(self):
        self.vault.change_any_state(key='testing', new_value='testing')
        assert self.vault.vaults['testing'] == 'testing'
        self.vault.change_any_state(key='testing', new_value='again')
        assert self.vault.vaults['testing'] == 'again'

    def test_state_unauthorised(self):
        with self.assertRaisesRegex(AssertionError, 'owner'):
            self.vault.change_state(
                key='testing2', new_value='testing2', signer='me')

    def test_change_owner_works(self):
        self.vault.change_state(key='OWNER', new_value='stu')
        self.assertEqual(self.vault.vaults['OWNER'], 'stu')

        self.vault.change_state(key='OWNER', new_value='jeff', signer='stu')
        self.assertEqual(self.vault.vaults['OWNER'], 'jeff')

        self.vault.change_state(key='FOO', new_value='1',
                                convert_to_decimal=True, signer='jeff')
        self.assertEqual(self.vault.vaults['FOO'], 1)

    def test_change_owner_twice_fails(self):
        self.vault.change_state(key='OWNER', new_value='stu')
        self.assertEqual(self.vault.vaults['OWNER'], 'stu')

        with self.assertRaises(AssertionError):
            self.vault.change_state(key='OWNER', new_value='stu')

    def test_state_invalid_type_key(self):
        with self.assertRaisesRegex(AssertionError, 'key'):
            self.vault.change_state(key=42, new_value='value')

    def test_state_invalid_type_value(self):
        with self.assertRaisesRegex(AssertionError, 'value'):
            self.vault.change_state(key='value', new_value=42)

    def test_state_decimal(self):
        self.vault.change_state(
            key='testing2', new_value='0.42', convert_to_decimal=True)
        self.assertAlmostEqual(self.vault.vaults['testing2'], 0.42)

    def test_state_normal(self):
        self.vault.change_state(key='testing2', new_value='testing2')
        assert self.vault.vaults['testing2'] == 'testing2'
        self.vault.change_state(key='testing2', new_value='again2')
        assert self.vault.vaults['testing2'] == 'again2'

    def test_sync_burn_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'available'):
            self.vault.sync_burn(vault_type=-1, amount=1)

    def test_sync_burn_insufficient(self):
        with self.assertRaisesRegex(AssertionError, 'enough'):
            self.vault.sync_burn(vault_type=0, amount=1)

    def test_sync_burn_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.sync_burn(vault_type=0, amount=1)

    def test_sync_burn_changes_state(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        total = self.dai.total_supply.get()
        original = self.vault.vaults[0, 'total']
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.sync_burn(vault_type=0, amount=1)

        self.assertAlmostEqual(total - 1, self.dai.total_supply.get())
        self.assertAlmostEqual(original - 1, self.vault.vaults[0, 'total'])

    def test_sync_stability_pool_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'available'):
            self.vault.sync_stability_pool(vault_type=-1)

    def test_sync_stability_pool_zero(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.sync_stability_pool(vault_type=0)
        assert 0 == self.vault.stability_pool[0]

    def test_sync_stability_pool_positive(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)
        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.vault.settle_force_close(cdp_number=self.id, environment=env)
        self.vault.sync_stability_pool(vault_type=0)

    def test_sync_stability_pool_positive_changes_state(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)
        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.vault.settle_force_close(cdp_number=self.id, environment=env)
        total = self.vault.vaults[0, 'total']
        issued = self.vault.vaults[0, 'issued']
        pool = self.vault.stability_pool[0]
        self.assertAlmostEqual(self.vault.sync_stability_pool(
            vault_type=0), (issued + pool) / total)
        self.assertAlmostEqual(issued + pool, self.vault.vaults[0, 'issued'])
        self.assertAlmostEqual(self.vault.stability_pool[0], 0)

    def test_sync_stability_pool_negative(self):
        self.vault.vaults[0, 'total'] = 0
        self.vault.vaults[0, 'issued'] = 100
        self.vault.sync_stability_pool(vault_type=0)

    def test_sync_stability_pool_negative_changes_state(self):
        self.vault.vaults[0, 'total'] = 0
        self.vault.vaults[0, 'issued'] = 100
        self.vault.sync_stability_pool(vault_type=0)
        self.assertAlmostEqual(self.vault.vaults[0, 'issued'], 0)
        self.assertAlmostEqual(self.vault.stability_pool[0], 100)

    def test_remove_vault_unauthorised(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500)
        with self.assertRaisesRegex(AssertionError, 'owner'):
            self.vault.remove_vault(vault_type=0, signer='bob')

    def test_remove_vault_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500)
        self.vault.remove_vault(vault_type=0)
        assert 0 not in self.vault.vaults['list']

    def test_close_vault_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)

    def test_close_vault_closes_vault(self):
        self.currency.approve(to='vault_contract', amount=1500)

        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)

        self.assertEqual(self.vault.cdp[id, 'open'], False)

    def test_close_vault_updates_reserves(self):
        self.currency.approve(to='vault_contract', amount=1500)

        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)

        self.assertEqual(self.vault.vaults[0, 'issued'], 100)
        self.assertEqual(self.vault.vaults[0, 'total'], 100)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)

        self.assertEqual(self.vault.vaults[0, 'issued'], 0)
        self.assertEqual(self.vault.vaults[0, 'total'], 0)

    def test_close_vault_takes_dai(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)

        self.assertEqual(self.vault.vaults[0, 'issued'], 100)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)

    def close_vault_takes_dai_and_stability_fee(self):
        pass

    def close_vault_adjusts_based_on_reserves(self):  # use ENV
        pass

    # use ENV
    def close_vault_adjusts_based_on_reserves_and_stability_fee(self):
        pass

    def test_close_vault_returns_collateral(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)

        self.assertAlmostEqual(
            self.currency.balance_of(account='sys'),
            2147483647 - 1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)
        self.assertAlmostEqual(
            self.currency.balance_of(account='sys'),
            2147483647)

    def test_close_vault_funds_burned(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.assertAlmostEqual(self.dai.total_supply.get(), 100)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)
        self.assertAlmostEqual(self.dai.total_supply.get(), 0)

    def close_vault_fee_not_burned(self):
        pass

    def test_close_vault_unauthorised(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        with self.assertRaisesRegex(AssertionError, 'owner'):
            self.vault.close_vault(cdp_number=id, signer='wallet2')

    def test_close_vault_twice_fails(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)
        with self.assertRaisesRegex(AssertionError, 'closed'):
            self.vault.close_vault(cdp_number=id)

    def test_open_and_close_vault_1000_times(self):
        id_list = [i for i in range(1000)]

        for x in range(1, 1001):
            self.currency.approve(to='vault_contract',
                                  amount=151)
            self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                    amount_of_collateral=151)
            self.assertEqual(self.vault.vaults[0, 'issued'], x * 100)
            self.assertEqual(self.vault.vaults[0, 'total'], x * 100)
            self.assertEqual(self.dai.balances['sys'], x * 100)
            self.assertEqual(self.dai.total_supply.get(), x * 100)

        for x in range(1, 1001):
            id = random.choice(id_list)
            id_list.remove(id)
            self.dai.approve(to='vault_contract', amount=100)
            self.vault.close_vault(cdp_number=id)

            self.assertEqual(
                self.vault.vaults[0, 'issued'],
                1000 * 100 - x * 100)
            self.assertEqual(
                self.vault.vaults[0, 'total'],
                1000 * 100 - x * 100)
            self.assertEqual(self.dai.balances['sys'], 1000 * 100 - x * 100)
            self.assertEqual(self.dai.total_supply.get(), 1000 * 100 - x * 100)

    def test_timestamp_is_correct(self):
        assert abs(datetime.datetime.utcnow().timestamp() -
                   self.vault.get_timestamp()) % 14400 < 120

    def test_export_rewards_unauthorised(self):
        with self.assertRaisesRegex(AssertionError, 'owner'):
            self.vault.export_rewards(vault_type=0, amount=1, signer='wallet2')

    def test_export_rewards_insufficient(self):
        with self.assertRaisesRegex(AssertionError, 'enough'):
            self.vault.export_rewards(vault_type=0, amount=1)

    def test_export_rewards_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)
        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.vault.settle_force_close(cdp_number=self.id, environment=env)
        self.vault.export_rewards(vault_type=0, amount=0.1)

    def test_export_rewards_gives_rewards(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)
        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.vault.settle_force_close(cdp_number=self.id, environment=env)
        self.vault.export_rewards(vault_type=0, amount=0.1)
        self.assertAlmostEqual(self.dai.balance_of(account='sys'),
                               99.1)  # 99 from unused dai amount

    def test_export_rewards_changes_state(self):
        self.currency.approve(to='vault_contract', amount=1500)
        self.id = self.vault.create_vault(
            vault_type=0, amount_of_dai=100, amount_of_collateral=1500)
        self.vault.open_force_close_auction(cdp_number=self.id)
        self.dai.approve(to='vault_contract', amount=1)
        self.vault.bid_on_force_close(cdp_number=self.id, amount=1)
        env = {'now': Datetime(year=2022, month=12, day=31)}  # mocks the date
        self.vault.settle_force_close(cdp_number=self.id, environment=env)
        self.vault.export_rewards(vault_type=0, amount=0.1)
        assert self.vault.stability_pool[0] == 0

    def test_mint_rewards_unauthorised(self):
        with self.assertRaisesRegex(AssertionError, 'owner'):
            self.vault.mint_rewards(amount=1, signer='wallet2')

    def test_mint_rewards_negative(self):
        with self.assertRaisesRegex(AssertionError, 'negative'):
            self.vault.mint_rewards(amount=-1)

    def test_mint_rewards_normal(self):
        self.vault.mint_rewards(amount=1)

    def test_mint_rewards_gives_rewards(self):
        self.vault.mint_rewards(amount=1)
        self.assertAlmostEqual(self.dai.balance_of(account='sys'), 1)

    def test_mint_rewards_changes_state(self):
        self.vault.mint_rewards(amount=1)
        assert self.vault.vaults[0, 'total'] == 1

    def test_mint_rewards_floating_point(self):
        total = 0
        for _ in range(1000):
            minting = random.random() * 100
            total += minting
            self.vault.mint_rewards(amount=minting)
        self.assertAlmostEqual(self.vault.vaults[0, 'total'], total)

    def test_get_collateralization_percent_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.get_collateralization_percent(cdp_number=1)

    def test_get_collateralization_percent_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.assertAlmostEqual(
            self.vault.get_collateralization_percent(cdp_number=id), 15)

    def test_change_stability_rate_unauthorised(self):
        with self.assertRaisesRegex(AssertionError, 'owner'):
            self.vault.change_stability_rate(
                key=0, new_value=1.2, signer='wallet2')

    def test_change_stability_rate_normal(self):
        assert self.vault.stability_rate[0] == 1.1
        self.vault.change_stability_rate(key=0, new_value=1.2)
        assert self.vault.stability_rate[0] == 1.2

    def test_fast_force_close_vault_closed(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.vault.close_vault(cdp_number=id)
        with self.assertRaisesRegex(AssertionError, 'closed'):
            self.vault.fast_force_close_vault(cdp_number=id)

    def test_fast_force_close_vault_nonexistent(self):
        with self.assertRaisesRegex(AssertionError, 'cdp'):
            self.vault.fast_force_close_vault(cdp_number=id)

    def test_fast_force_close_vault_above_minimum(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        with self.assertRaisesRegex(AssertionError, 'above'):
            self.vault.fast_force_close_vault(cdp_number=id)

    def test_fast_force_close_vault_under_103_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.oracle.set_price(number=0, new_price=0.01)
        self.vault.fast_force_close_vault(cdp_number=id)

    def test_fast_force_close_vault_above_103_normal(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.mint(amount=10, signer='vault_contract') # since we set dsr owner in setup
        self.dai.transfer(amount=10, to='sys', signer='vault_contract')
        self.dai.approve(to='vault_contract', amount=110)
        self.oracle.set_price(number=0, new_price=0.09)
        self.vault.fast_force_close_vault(cdp_number=id)

    def test_fast_force_close_vault_takes_money(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.oracle.set_price(number=0, new_price=0.01)
        self.vault.fast_force_close_vault(cdp_number=id)
        assert self.dai.balance_of(account='sys') < 100

    def test_fast_force_close_vault_under_103_changes_state(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.approve(to='vault_contract', amount=100)
        self.oracle.set_price(number=0, new_price=0.01)
        issued = self.vault.vaults[self.vault.cdp[0, 'vault_type'], 'issued']
        total = self.vault.vaults[self.vault.cdp[0, 'vault_type'], 'total']
        self.vault.fast_force_close_vault(cdp_number=id)

        redemption_cost_without_fee = (100) * (1500 * 0.01 / (100 * 1.1)) / 1.03 # original, dai minted, collateral percent, collateral reward respectively
        self.assertAlmostEqual(self.dai.balance_of(account='sys'), 100 - redemption_cost_without_fee * 1.1)
        self.assertAlmostEqual(self.dai.total_supply.get(), 100 - redemption_cost_without_fee)
        self.assertAlmostEqual(self.currency.balance_of(account='sys'), 2147483647) # reward to closer
        self.assertAlmostEqual(issued - 100, self.vault.vaults[self.vault.cdp[0, 'vault_type'], 'issued'])
        self.assertAlmostEqual(total - redemption_cost_without_fee, self.vault.vaults[self.vault.cdp[0, 'vault_type'], 'total'])
        self.assertAlmostEqual(self.dai.balance_of(account='vault_contract'), self.vault.stability_pool[self.vault.cdp[0, 'vault_type']])

    def test_fast_force_close_vault_above_103_changes_state(self):
        self.currency.approve(to='vault_contract', amount=1500)
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                     amount_of_collateral=1500)
        self.dai.mint(amount=10, signer='vault_contract') # since we set dsr owner in setup
        self.dai.transfer(amount=10, to='sys', signer='vault_contract')
        self.dai.approve(to='vault_contract', amount=110)
        self.oracle.set_price(number=0, new_price=0.09)
        issued = self.vault.vaults[self.vault.cdp[0, 'vault_type'], 'issued']
        total = self.vault.vaults[self.vault.cdp[0, 'vault_type'], 'total']
        self.vault.cdp[0, 'owner'] = 'wallet2'
        self.vault.fast_force_close_vault(cdp_number=id)

        redemption_cost_without_fee = 100
        self.assertAlmostEqual(self.dai.balance_of(account='sys'), 110 - redemption_cost_without_fee * 1.1)
        self.assertAlmostEqual(self.dai.total_supply.get(), 110 - redemption_cost_without_fee)
        self.assertAlmostEqual(self.currency.balance_of(account='sys'), 2147483647 - 1500 + (1 / 0.09) * 100 * 1.03) # reward to closer
        self.assertAlmostEqual(self.currency.balance_of(account='wallet2'), 1500 - (1 / 0.09) * 100 * 1.03) # reward to owner
        self.assertAlmostEqual(issued - 100, self.vault.vaults[self.vault.cdp[0, 'vault_type'], 'issued'])
        self.assertAlmostEqual(total - redemption_cost_without_fee, self.vault.vaults[self.vault.cdp[0, 'vault_type'], 'total'])
        self.assertAlmostEqual(self.dai.balance_of(account='vault_contract'), self.vault.stability_pool[self.vault.cdp[0, 'vault_type']])
