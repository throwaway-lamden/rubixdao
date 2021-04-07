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

# TODO: Update this to the new method
add_vault(collateral_type='currency', # TAU
              collateral_amount=1.5, # you need $1.5 of TAU for every $1 of DAI minted
              max_minted=100000, # only 100000 DAI can ever be minted
              weight=10) # used to determine how much staking rewards inflate the pools relative to other vaults
```

### get_timestamp

**Cannot be called**

Returns current UTC timestamp.

### create_vault
Takes `vault_type: int, amount_of_dai: float, amount_of_collateral: float`

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

### close_vault
Takes `cdp_number: int`

Closes a vault. Transfers original DAI and additional fee from caller to contract and returns original collateral to caller. 

If the amount of currently circulating DAI is greater than the amount of DAI in the open vaults (this can happen if a lot of vaults are liquidated at prices below 1x), the redemption cost is multiplied by (circulating DAI / DAI issued by currently open vaults).

#### Checks: 

- Asserts the owner is the caller of the vault
- Asserts the vault is not closed

Returns the amount of DAI transferred to the contract.

### fast_force_close_vault
Takes `cdp_number: int`

Closes an undercollateralized vault instantly with a small reward (3.3%) issued to the closer and a 10% penalty added to the stability pool. 

If the value of the collateral is greater than 113.3% of the DAI borrowed, the liquidator returns 110% of the DAI and recieves 113.3% equivalent value in collateral. The remaining collateral is returned to the CDP owner. 9.09% of the returned DAI is added to the stability pool and the remaining returned DAI is burned normally. Total DAI and Issued DAI for the vault type are both updated with the burn amount.

If the value of the collateral is less than 113.3% of the DAI borrowed, the liquidator recieves all the collateral and returns 97.1% of the equivalent value in DAI. 9.09% of the returned DAI is added to the stability pool and the remaining returned DAI is burned normally. Total DAI is updated with the original amount of DAI in the vault. Issued DAI is updated with the burned amount.

#### Checks: 

- Asserts the vault does not have sufficent collateral
- Asserts the vault is not closed

Returns the amount of collateral paid out.

### open_force_close_auction
Takes `cdp_number: int`

Opens an auction for an undercollateralized vault. Sets `cdp[cdp_number, 'open']` to `False` and `cdp[cdp_number, 'auction', 'open']` to `True`. Gets the auction start time with `get_timestamp()` and stores it under `cdp[cdp_number, 'auction', 'time']`.

#### Checks: 

- Asserts the vault exists and is open

Returns `True`.

### bid_on_force_close
Takes `cdp_number: int, amount: float`

Bids on the specified vault with `amount` DAI. If the caller has previously bid, the amount transferred is `amount` minus previous bid. Otherwise, the amount transferred is just the specified `amount`.

#### Checks: 

- Asserts that `amount` is the highest bid
- Asserts the vault exists and the auction is open

Returns `True`.

### settle_force_close
Takes `cdp_number: int`

Closes the auction specified. Sends 90% of the collateral to the top bidder and 10% to the stability pool of the specific vault. Sets `cdp[cdp_number, 'auction', 'open']` to `False`.

#### Checks: 

- Asserts the time elapsed from the start of the auction is longer than the minimum auction time for the vault type
- Asserts the vault exists and the auction is open

Returns a tuple with the top bidder address and the top bid.

### claim_unwon_bid
Takes `cdp_number: int`

Returns the DAI bid of the specified auction to the caller. 

#### Checks: 

- Asserts the auction is over

Returns `True`.

### sync_stability_pool
Takes `vault_type: int`

Tries to equalize circulating DAI with DAI issued by currently open vaults. 

If the stability pool contains more DAI than the difference between circulating DAI and issued DAI, the difference is equalized and subtracted from the stability pool. 
Otherwise, the entire stability pool is transferred to the issued DAI pool to equalize the ratio as much as possible.

#### Checks: 

- N/A

Returns (circulating DAI / DAI issued by currently open vaults).

### export_rewards
Takes `vault_type: int, amount: float`

Transfers out a specified amount of the stability pool to the caller. Intended use is to pay out rewards to lMKR holders, but anything can be done with this.

#### Checks: 

- Asserts the caller is the address specified in `vaults[vault_type, 'DSR', 'owner']`
- Asserts there is sufficent DAI in the stability pool

Returns `True`.


### mint_rewards
Takes `vault_type: int, amount: float`

Description.

#### Checks: 

- Asserts 
- Asserts 

Returns .


### sync_burn
Takes `vault_type: int, amount: float`

Description.

#### Checks: 

- Asserts 
- Asserts 

Returns .


### add_vault
Takes `collateral_type: str, collateral_amount: float, auction_time: float, max_minted: float, s_rate: float, weight: float)`

Description.

#### Checks: 

- Asserts 
- Asserts 

Returns .


### remove_vault
Takes `vault_type: int`

Description.

#### Checks: 

- Asserts 
- Asserts 

Returns .

### change_state
Takes `key: str, new_value: str, convert_to_decimal: bool = False`

Description.

#### Checks: 

- Asserts 
- Asserts 

Returns .

### get_collateralization_percent
Takes `cdp_number: int`

Description.

#### Checks: 

- Asserts 
- Asserts 

Returns .
