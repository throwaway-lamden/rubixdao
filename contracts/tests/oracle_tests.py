import unittest

from contracting.client import ContractingClient


class OracleTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('oracle.py') as file:
            code = file.read()
        self.client.submit(code, name='oracle')
        self.oracle = self.client.get_contract('oracle')

    def tearDown(self):
        self.client.flush()

    def test_oracle(self):
        assert self.oracle.get_price(number=0) == 0
        try:
            self.oracle.set_price(number=0, new_price=-1)
            raise
        except AssertionError as message:
            assert 'negative' in str(message)
        self.oracle.set_price(number=0, new_price=1)
        assert self.oracle.get_price(number=0) == 1

if __name__ == '__main__':
    unittest.main()
