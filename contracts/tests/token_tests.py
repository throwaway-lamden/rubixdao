import unittest

from contracting.client import ContractingClient


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('dai_token.py') as file:
            code = file.read()
        self.client.submit(code, name='dai_token', constructor_args={
                           'vk': 'me', 'owner': 'default_owner'})
        self.token = self.client.get_contract('dai_token')

    def tearDown(self):
        self.client.flush()

    def test_transfer(self):
        try:
            self.token.transfer(amount=-1, to='wallet2', signer='me')
            raise
        except AssertionError as message:
            assert 'negative' in str(message)
        try:
            self.token.transfer(amount=1000001, to='wallet2', signer='me')
            raise
        except AssertionError as message:
            assert 'enough' in str(message)
        self.token.transfer(amount=42, to='wallet2', signer='me')
        assert self.token.balance_of(account='me') == 1000000 - 42
        assert self.token.balance_of(account='wallet2') == 42

    def test_balance(self):
        assert self.token.balance_of(account='me') == 1000000
        assert self.token.balance_of(account='wallet2') == 0

    def test_owner(self):
        try:
            self.token.change_owner(new_owner='wallet2', signer='wallet2')
            raise
        except AssertionError as message:
            assert 'operator' in str(message)
        self.token.change_owner(new_owner='wallet2', signer='default_owner')
        try:
            self.token.change_owner(new_owner='me', signer='me')
            raise
        except AssertionError as message:
            assert 'operator' in str(message)

    def test_supply(self):
        old_supply = self.token.get_total_supply()
        try:
            self.token.burn(amount=-1, signer='me')
            raise
        except AssertionError as message:
            assert 'negative' in str(message)
        try:
            self.token.burn(amount=1000001, signer='me')
            raise
        except AssertionError as message:
            assert 'enough' in str(message)
        self.token.burn(amount=42, signer='me')
        assert self.token.get_total_supply() == old_supply - 42
        try:
            self.token.mint(amount=42, signer='me')
            raise
        except AssertionError as message:
            assert 'operator' in str(message)
        try:
            self.token.mint(amount=-1, signer='default_owner')
            raise
        except AssertionError as message:
            assert 'negative' in str(message)
        self.token.mint(amount=42, signer='default_owner')
        assert self.token.get_total_supply() == old_supply

    def test_metadata(self):
        try:
            self.token.change_metadata(key='testing', value='testing', signer='me')
            raise
        except AssertionError as message:
            assert 'operator' in str(message)
        self.token.change_metadata(key='testing', value='testing')
        assert self.token.metadata['testing'] == 'testing'
        self.token.change_metadata(key='testing', value='again')
        assert self.token.metadata['testing'] == 'again'
        
if __name__ == '__main__':
    unittest.main()
