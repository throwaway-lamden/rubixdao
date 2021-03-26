import unittest

from contracting.client import ContractingClient


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('dai_token.py') as file:
            code = file.read()
        self.client.submit(code, name='dai_token', constructor_args={'vk': 'me', 'owner': 'default_owner'})
        self.token = self.client.get_contract('dai_token')

    def tearDown(self):
        self.client.flush()

    def test_balance(self):
        assert self.token.balance_of(account="me") == 1000000
        assert self.token.balance_of(account="new_user") == 0

    def test_transfer(self):
        try:
            self.token.transfer(amount=-1, to="receiver", signer="me")
        except AssertionError as message:
            assert 'negative' in str(message)
        try:
            self.token.transfer(amount=1000001, to="receiver", signer="me")
        except AssertionError as message:
            assert 'enough' in str(message)
        self.token.transfer(amount=42, to="receiver", signer="me")
        assert self.token.balance_of(account="me") == 1000000 - 42
        assert self.token.balance_of(account="receiver") == 42

if __name__ == "__main__":
    unittest.main()
