import datetime
import unittest

from contracting.client import ContractingClient


class StakingTests(unittest.TestCase):
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
        with open('staking.py') as file:
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

    def 
    def test_timestamp(self):
        assert abs(datetime.datetime.utcnow().timestamp() -
                   self.staking.get_timestamp()) < 120


if __name__ == '__main__':
    unittest.main()
