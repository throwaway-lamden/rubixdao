# Lamden MKR Contracts

## vault.py functions

### seed

**Cannot be called**

Sets the constants to their default value. As of now, you cannot pass arguments, and you have to manually modify the code.

The default values are as follows:
```python
vaults['OWNER'] = ctx.caller
cdp['current_value'] = 0    
vaults['oracle'] = 'oracle'  # the contract will pull all price data from 'oracle'. Please change this prior to deployment
vaults['stability_rate'] = 1.1 # dummy for testing
add_vault(collateral_type='currency', # TAU
              collateral_amount=1.5, # you need $1.5 of TAU for every $1 of DAI minted
              max_minted=100000, # only 100000 DAI can ever be minted
              weight=10) # used to determine how much staking rewards inflate the pools relative to other vaults
```

### get_timestamp()

**Cannot be called**

Returns current UTC timestamp.

### create_vault(vault_type: int, amount_of_dai: float, amount_of_collateral: float)

Creates a vault. Issues DAI and transfers collateral from caller to contract if the following checks pass.

#### Checks: 

- Asserts that the vault type is in the list of approved vaults
- Asserts that the amount of DAI is positive
- Asserts that the amount is not greater than the max_minted value of the vault
- Asserts that the collateral multiplied by the oracle price is greater than the minimum collateral for the vault type

Returns the vault id.
