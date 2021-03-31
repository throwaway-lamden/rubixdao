import unittest

from contracting.client import ContractingClient


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('dai_token.py') as file:
            code = file.read()
        self.client.submit(code, name='dai_token', constructor_args={
                           'owner': 'me'})
        self.token = self.client.get_contract('dai_token')

        self.token.mint(amount=1000000, signer='me')

    def tearDown(self):
        self.client.flush()

    def test_transfer_negative(self):
        try:
            self.token.transfer(amount=-1, to='wallet2', signer='me')
            raise
        except AssertionError as message:
            assert 'non-positive' in str(message)

    def test_transfer_excess(self):
        try:
            self.token.transfer(amount=1000001, to='wallet2', signer='me')
            raise
        except AssertionError as message:
            assert 'enough' in str(message)

    def test_transfer_normal(self):
        self.token.transfer(amount=42, to='wallet2', signer='me')
        self.assertAlmostEqual(
            self.token.balance_of(account='me'), 1000000 - 42)
        self.assertAlmostEqual(self.token.balance_of(account='wallet2'), 42)

    def test_balance(self):
        self.assertAlmostEqual(self.token.balance_of(account='me'), 1000000)
        self.assertAlmostEqual(self.token.balance_of(account='wallet2'), 0)

    def test_accounts_negative(self):
        try:
            self.token.approve(amount=-1, to='account1', signer='me')
            raise
        except AssertionError as message:
            assert 'non-positive' in str(message)

    def test_accounts_excess(self):
        try:
            self.token.approve(amount=1000001, to='account1', signer='me')
            raise
        except AssertionError as message:
            assert 'exceeds' in str(message)

    def test_accounts_normal(self):
        self.token.approve(amount=42, to='account1', signer='me')
        self.assertAlmostEqual(self.token.allowance(
            owner='me', spender='account1', signer='me'), 42)

    def test_transfer_from_negative(self):
        self.token.approve(amount=42, to='account1', signer='me')
        try:
            self.token.transfer_from(amount=-1, to='wallet2',
                                     main_account='me', signer='account1')
            raise
        except AssertionError as message:
            assert 'non-positive' in str(message)

    def test_transfer_from_excess(self):
        self.token.approve(amount=42, to='account1', signer='me')
        try:
            self.token.transfer_from(amount=1000001, to='wallet2',
                                     main_account='me', signer='account1')
            raise
        except AssertionError as message:
            assert 'enough' in str(message)

    def test_transfer_from_approved(self):
        self.token.approve(amount=42, to='account1', signer='me')
        try:
            self.token.transfer_from(amount=1000000, to='wallet2',
                                     main_account='me', signer='account1')
            raise
        except AssertionError as message:
            assert 'approved' in str(message)

    def test_transfer_from_normal(self):
        self.token.approve(amount=42, to='account1', signer='me')
        self.token.transfer_from(amount=42, to='wallet2',
                                 main_account='me', signer='account1')
        self.assertAlmostEqual(self.token.allowance(
            owner='me', spender='account1', signer='me'), 0)
        self.assertAlmostEqual(
            self.token.balance_of(account='me'), 1000000 - 42)
        self.assertAlmostEqual(self.token.balance_of(account='wallet2'), 42)

    def test_burn_negative(self):
        try:
            self.token.burn(amount=-1, signer='me')
            raise
        except AssertionError as message:
            assert 'non-positive' in str(message)

    def test_burn_excess(self):
        try:
            self.token.burn(amount=1000001, signer='me')
            raise
        except AssertionError as message:
            assert 'enough' in str(message)

    def test_burn_normal(self):
        old_supply = self.token.get_total_supply()
        self.token.burn(amount=42, signer='me')
        self.assertAlmostEqual(self.token.get_total_supply(), old_supply - 42)

    def test_mint_negative(self):
        try:
            self.token.mint(amount=-1, signer='me')
            raise
        except AssertionError as message:
            assert 'non-positive' in str(message)

    def test_mint_unauthorised(self):
        try:
            self.token.mint(amount=42, signer='wallet1')
            raise
        except AssertionError as message:
            assert 'operator' in str(message)

    def test_mint_normal(self):
        old_supply = self.token.get_total_supply()
        self.token.mint(amount=42, signer='me')
        self.assertAlmostEqual(self.token.get_total_supply(), old_supply + 42)

    def test_metadata_unauthorised(self):
        try:
            self.token.change_metadata(
                key='testing', value='testing', signer='me')
            raise
        except AssertionError as message:
            assert 'operator' in str(message)

    def test_metadata_normal(self):
        self.token.change_metadata(key='testing', value='testing')
        assert self.token.metadata['testing'] == 'testing'
        self.token.change_metadata(key='testing', value='again')
        assert self.token.metadata['testing'] == 'again'

    def test_change_owner_unauthorised(self):
        try:
            self.token.change_owner(new_owner='wallet2', signer='wallet2')
            raise
        except AssertionError as message:
            assert 'operator' in str(message)

    def test_change_owner_normal(self):
        self.token.change_owner(new_owner='wallet2', signer='me')
        try:
            self.token.change_owner(new_owner='me', signer='me')
            raise
        except AssertionError as message:
            assert 'operator' in str(message)


if __name__ == '__main__':
    unittest.main()
