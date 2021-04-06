# Lamden MKR Contracts

## vault.py functions

### seed()

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

Updates total issued DAI for that vault type. 

Sets the following information for the newly opened vault:

```python
    cdp[cdp_number, 'owner'] = ctx.caller
    cdp[cdp_number, 'open'] = True

    cdp[cdp_number, 'collateral_type'] = vaults[vault_type, 'collateral_type']
    cdp[cdp_number, 'vault_type'] = vault_type
    cdp[cdp_number, 'dai'] = amount_of_dai
    cdp[cdp_number, 'collateral_amount'] = amount_of_collateral
    cdp[cdp_number, 'time'] = get_timestamp()
```

#### Checks: 

- Asserts that the vault type is in the list of approved vaults
- Asserts that the amount of DAI is positive
- Asserts that the amount is not greater than the max_minted value of the vault
- Asserts that the collateral multiplied by the oracle price is greater than the minimum collateral for the vault type

Returns the vault id.

### close_vault(cdp_number: int)

Closes a vault. Transfers original DAI and additional fee from caller to contract and returns original collateral to caller.

#### Checks: 

- Asserts the owner is the caller of the vault
- Asserts the vault is not closed

Returns the amount of DAI transferred to the contract.

### fast_force_close_vault(cdp_number: int)

Closes an undercollateralized vault instantly with a small reward (3.3%) issued to the closer and a 10% penalty added to the stability pool. 

If the value of the collateral is greater than 113.3% of the DAI borrowed, the liquidator returns 110% of the DAI and recieves 113.3% equivalent value in collateral. The remaining collateral is returned to the CDP owner. 9.09% of the returned DAI is added to the stability pool and the remaining returned DAI is burned normally. Total DAI and Issued DAI for the vault type are both updated with the burn amount.

If the value of the collateral is less than 113.3% of the DAI borrowed, the liquidator recieves all the collateral and returns 97.1% of the equivalent value in DAI. 9.09% of the returned DAI is added to the stability pool and the remaining returned DAI is burned normally. Total DAI is updated with the original amount of DAI in the vault. Issued DAI is updated with the burned amount.

#### Checks: 

- Asserts the vault does not have sufficent collateral
- Asserts the vault is not closed

Returns the amount of collateral paid out.
