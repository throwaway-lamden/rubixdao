import unittest

from contracting.client import ContractingClient

client = ContractingClient()


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('dai_token.py') as file:
            dai = file.read()
        with open('basic_vault.py') as file:
            vault = file.read()
        self.client.submit(dai, name='dai_contract', constructor_args={
                           'vk': 'me', 'owner': 'default_owner'})
        self.client.submit(vault, name='vault_contract')
        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')

    def tearDown(self):
        self.client.flush()

    def test_state(self):
        try:
            self.vault.change_any_state(
                key='testing', new_value='testing', signer='me')
            raise
        except AssertionError as message:
            assert 'owner' in str(message)
        self.vault.change_any_state(key='testing', new_value='testing')
        assert self.vault.vaults['testing'] == 'testing'
        self.vault.change_any_state(key='testing', new_value='again')
        assert self.vault.vaults['testing'] == 'again'

        try:
            self.vault.change_state(
                key='testing2', new_value='testing2', signer='me')
            raise
        except AssertionError as message:
            assert 'owner' in str(message)
        try:
            # int is invalid value
            self.vault.change_state(key='testing2', new_value=5)
            raise NotImplementedError  # we shouldn't get to here
        except Exception as message:
            assert 'NotImplementedError' not in str(message)

        self.vault.change_state(key='testing2', new_value='testing2')
        assert self.vault.vaults['testing2'] == 'testing2'
        self.vault.change_state(key='testing2', new_value='again2')
        assert self.vault.vaults['testing2'] == 'again2'
        self.vault.change_state(
            key='testing2', new_value='0.42', convert_to_decimal=True)
        self.assertAlmostEqual(self.vault.vaults['testing2'], 0.42)
