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
                           'vk': 'me', 'owner': 'vault_contract'})
        
        self.client.submit(vault, name='vault_contract')
        self.client.submit(currency, name='currency')
        self.client.submit(oracle, name='oracle')
        
        self.dai = self.client.get_contract('dai_contract')
        self.vault = self.client.get_contract('vault_contract')
        self.currency = self.client.get_contract("currency")
        self.oracle = self.client.get_contract("oracle")

        # self.dai.change_owner(new_owner="vault_contract")
        
    def tearDown(self):
        self.client.flush()

    def test_create_vault_unavailable(self):
        try:
            self.vault.create_vault(
                vault_type=-1, amount_of_dai=100, amount_of_collateral=100)
            raise
        except AssertionError as message:
            assert 'available' in str(message)

    def test_create_vault_negative(self):
        try:
            self.vault.create_vault(vault_type=0, amount_of_dai=-
                                    1,  amount_of_collateral=100)
            raise
        except AssertionError as message:
            assert 'positive' in str(message)

    def test_create_vault_insufficient_allowance(self):
        try:
            self.vault.create_vault(
                vault_type=0, amount_of_dai=1000001,  amount_of_collateral=1000001)
            raise
        except AssertionError as message:
            assert 'allowance' in str(message)

    def test_create_vault_insufficient_collateral(self):
        try:
            self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                    amount_of_collateral=100)
            raise
        except AssertionError as message:
            assert 'collateral' in str(message)

    def test_create_vault_normal(self):
        # pass
        self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500) # Might fail, not sure why commented

    def test_create_vault_takes_collateral(self):
        self.currency.transfer(to="stu", amount=1500)
        
        self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500, signer="stu") # Might fail, not sure why commented
        
        self.assertEquals(self.currency.balances["stu"], 0)
    
    def test_create_vault_gives_dai(self):
        self.currency.transfer(to="stu", amount=1500)
        
        self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500, signer="stu") # Might fail, not sure why commented
        
        self.assertEquals(self.dai.balances["stu"], 100)
        
    def test_create_vault_updates_reserves(self):
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500)
        
        self.assertEquals(self.vault.cdp[id, "issued"], 100)
        self.assertEquals(self.vault.cdp[id, "total"], 100)
        
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

    def test_change_owner_works(self):
        self.vault.change_state(key="OWNER", new_value="stu")
        self.assertEqual(self.vault.state["OWNER"], "stu")
        
        self.vault.change_state(key="OWNER", new_value="jeff", signer="stu")
        self.assertEqual(self.vault.state["OWNER"], "jeff")
        
        self.vault.change_state(key="FOO", new_value=1, convert_to_decimal=True, signer="jeff")
        self.assertEqual(self.vault.state["FOO"], 1)
        
    def test_change_owner_twice_fails(self):
        self.vault.change_state(key="OWNER", new_value="stu")
        self.assertEqual(self.vault.state["OWNER"], "stu")
        
        with self.assertRaises(AssertionError):
            self.vault.change_state(key="OWNER", new_value="stu")
            
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
        
    def close_vault_works(self):
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500)
        
        self.vault.close_vault(cdp_number=id)
    
    def close_vault_closes_vault(self):
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500)
        
        self.vault.close_vault(cdp_number=id)
        
        self.assertEquals(self.vault.cdp[id, "open"], False)
    
    def close_vault_updates_reserves(self):
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500)
        
        self.assertEquals(self.vault.cdp[id, "issued"], 100)
        self.assertEquals(self.vault.cdp[id, "total"], 100)
        
        self.vault.close_vault(cdp_number=id)
        
        self.assertEquals(self.vault.cdp[id, "issued"], 0)
        self.assertEquals(self.vault.cdp[id, "total"], 0)
    
    def close_vault_takes_dai(self):
        pass
    
        # fix later
        id = self.vault.create_vault(vault_type=0, amount_of_dai=100,
                                amount_of_collateral=1500)
        
        self.assertEquals(self.vault.cdp[id, "issued"], 100)
        
        self.vault.close_vault(cdp_number=id)
    
    def close_vault_takes_dai_and_stability_fee(self):
        pass
    
    def close_vault_adjusts_based_on_reserves(self): # use ENV
        pass
    
    def close_vault_adjusts_based_on_reserves_and_stability_fee(self): # use ENV
        pass
    
    def close_vault_takes_dai(self):
        pass
    
    def close_vault_returns_collateral(self):
        pass
    
    def close_vault_funds_burned(self):
        pass
    
    def close_vault_fee_not_burned(self):
        pass
    
    def close_vault_unauthorised(self):
        pass
    
    def close_vault_twice_fails(self):
        pass
    
    
