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

        self.oracle.set_price(number=0, new_price=1.0)

    def tearDown(self):
        self.client.flush()

    def test_proper_test_setup(self):
        self.assertAlmostEqual(self.oracle.current_price[0], 1)

    def test_oracle_price_negative(self):
        with self.assertRaisesRegex(AssertionError, 'negative'):
            self.oracle.set_price(number=1, new_price=-1)

    def test_oracle_price_normal(self):
        self.assertAlmostEqual(self.oracle.get_price(number=1), 0)
        self.oracle.set_price(number=1, new_price=1)
        self.assertAlmostEqual(self.oracle.get_price(number=1), 1)


if __name__ == '__main__':
    unittest.main()
