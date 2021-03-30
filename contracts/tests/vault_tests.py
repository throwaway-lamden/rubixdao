import unittest

from contracting.client import ContractingClient


class VaultTests(unittest.TestCase):
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
        self.client.submit(currency, name='oracle')
        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')
        self.currency = self.client.get_contract("currency")
        self.oracle = self.client.get_contract("oracle")

    def tearDown(self):
        self.client.flush()

    def test_create_vault(self):
        try:
            self.vault.create_vault(vault_type=-1, amount_of_dai=100, amount_of_collateral=100)
            raise
        except AssertionError as message:
            assert 'available' in str(message)
        self.vault.create_vault(vault_type=0, amount_of_dai=100,  amount_of_collateral=100)
        # test for allowance
        # test for collateral

    def test_any_state_unauthorised(self):
        try:
            self.vault.change_any_state(
                key='testing', new_value='testing', signer='me')
            raise
        except AssertionError as message:
            assert 'owner' in str(message)

    def test_any_state_normal(self):
        self.vault.change_any_state(key='testing', new_value='testing')
        assert self.vault.vaults['testing'] == 'testing'
        self.vault.change_any_state(key='testing', new_value='again')
        assert self.vault.vaults['testing'] == 'again'

    def test_state_unauthorised(self):
        try:
            self.vault.change_state(
                key='testing2', new_value='testing2', signer='me')
            raise
        except AssertionError as message:
            assert 'owner' in str(message)

    def test_state_invalid_type(self):
        try:
            # int is invalid value
            self.vault.change_state(key='testing2', new_value=5)
            raise NotImplementedError  # we shouldn't get to here
        except Exception as message:
            assert 'NotImplementedError' not in str(message)

    def test_state_decimal(self):
        self.vault.change_state(
            key='testing2', new_value='0.42', convert_to_decimal=True)
        self.assertAlmostEqual(self.vault.vaults['testing2'], 0.42)

    def test_state_normal(self):
        self.vault.change_state(key='testing2', new_value='testing2')
        assert self.vault.vaults['testing2'] == 'testing2'
        self.vault.change_state(key='testing2', new_value='again2')
        assert self.vault.vaults['testing2'] == 'again2'
