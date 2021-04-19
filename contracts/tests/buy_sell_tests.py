import unittest

from contracting.client import ContractingClient


class BuySellTests(unittest.TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()
        with open('../keeper-examples/buy_and_sell.py') as file:
            code = file.read()
        self.client.submit(code, name='buysell')
        self.buysell = self.client.get_contract('buysell')

    def tearDown(self):
        self.client.flush()

    def test(self):
        pass


if __name__ == '__main__':
    unittest.main()
