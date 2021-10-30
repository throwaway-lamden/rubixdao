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

vaults[0, 'collateral_type'] = 'currency'
vaults[0, 'minimum_collateralization'] = 1.5
vaults[0, 'minimum_auction_time'] = 259200
vaults[0, 'cap'] = 100000
vaults[0, 'weight'] = 10

stability_rate[0] = 1.1  # dummy for testing purposes
```

### get_timestamp

**Cannot be called**

Returns current UTC timestamp.

### create_vault
Takes `vault_type: int, amount_of_tad: float, amount_of_collateral: float`

Creates a vault. Issues tad and transfers collateral from caller to contract if the following checks pass.

Updates total issued tad for that vault type.

Sets the following information for the newly opened vault:

```python
cdp[cdp_number, 'owner'] = ctx.caller
cdp[cdp_number, 'open'] = True

cdp[cdp_number, 'collateral_type'] = vaults[vault_type, 'collateral_type']
cdp[cdp_number, 'vault_type'] = vault_type
cdp[cdp_number, 'tad'] = amount_of_tad
cdp[cdp_number, 'collateral_amount'] = amount_of_collateral
cdp[cdp_number, 'time'] = get_timestamp()
```

#### Checks:

- Asserts that the vault type is in the list of approved vaults
- Asserts that the amount of tad is positive
- Asserts that the amount is not greater than the max_minted value of the vault
- Asserts that the collateral multiplied by the oracle price is greater than the minimum collateral for the vault type

Returns the vault id.

### close_vault
Takes `cdp_number: int`

Closes a vault. Transfers original tad and additional fee from caller to contract and returns original collateral to caller.

If the amount of currently circulating tad is greater than the amount of tad in the open vaults (this can happen if a lot of vaults are liquidated at prices below 1x), the redemption cost is multiplied by (circulating tad / tad issued by currently open vaults).

#### Checks:

- Asserts the owner is the caller of the vault
- Asserts the vault is not closed

Returns the amount of tad transferred to the contract.

### fast_force_close_vault
Takes `cdp_number: int`

Closes an undercollateralized vault instantly with a small reward (3.3%) issued to the closer and a 10% penalty added to the stability pool.

If the value of the collateral is greater than 113.3% of the tad borrowed, the liquidator returns 110% of the tad and recieves 113.3% equivalent value in collateral. The remaining collateral is returned to the CDP owner. 9.09% of the returned tad is added to the stability pool and the remaining returned tad is burned normally. Total tad and Issued tad for the vault type are both updated with the burn amount.

If the value of the collateral is less than 113.3% of the tad borrowed, the liquidator recieves all the collateral and returns 97.1% of the equivalent value in tad. 9.09% of the returned tad is added to the stability pool and the remaining returned tad is burned normally. Total tad is updated with the original amount of tad in the vault. Issued tad is updated with the burned amount.

#### Checks:

- Asserts the vault does not have sufficent collateral
- Asserts the vault exists and is open

Returns the amount of collateral paid out.

### open_force_close_auction
Takes `cdp_number: int`

Opens an auction for an undercollateralized vault. Sets `cdp[cdp_number, 'open']` to `False` and `cdp[cdp_number, 'auction', 'open']` to `True`. Gets the auction start time with `get_timestamp()` and stores it under `cdp[cdp_number, 'auction', 'time']`.

#### Checks:

- Asserts the vault exists and is open

Returns `True`.

### bid_on_force_close
Takes `cdp_number: int, amount: float`

Bids on the specified vault with `amount` tad. If the caller has previously bid, the amount transferred is `amount` minus previous bid. Otherwise, the amount transferred is just the specified `amount`.

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

Returns the tad bid of the specified auction to the caller.

#### Checks:

- Asserts the auction is over
- Asserts the vault exists

Returns `True`.

### sync_stability_pool
Takes `vault_type: int`

Tries to equalize circulating tad with tad issued by currently open vaults.

If the stability pool contains more tad than the difference between circulating tad and issued tad, the difference is equalized and subtracted from the stability pool.
Otherwise, the entire stability pool is transferred to the issued tad pool to equalize the ratio as much as possible.

#### Checks:

- N/A

Returns (circulating tad / tad issued by currently open vaults).

### export_rewards
Takes `vault_type: int, amount: float`

Transfers out a specified amount of the stability pool to the caller. Intended use is to pay out rewards to lMKR holders, but anything can be done with this.

#### Checks:

- Asserts the caller is the address specified in `vaults[vault_type, 'DSR', 'owner']`
- Asserts there is sufficent tad in the stability pool

Returns `True`.


### mint_rewards
Takes `vault_type: int, amount: float`

Calls `tad.py` to mint tad. Sends the tad to the caller, and updates total circulating tad for every vault based on the `weight` variable. Intended use is to pay rewards to stakers.

#### Checks:

- Asserts the caller is the address specified in `vaults[vault_type, 'DSR', 'owner']`

Returns `True`.


### sync_burn
Takes `vault_type: int, amount: float`

Removes the burn amount from the total circulating tad supply of a vault. This is intended to be used similarly to the MKR auction concept, where tad is bought and burned to reduce the cost of closing vaults.

#### Checks:

- N/A

Returns the new total circulating supply.


### add_vault
Takes `collateral_type: str, collateral_amount: float, auction_time: float, max_minted: float, s_rate: float, weight: float)`

Adds a vault with the following properties. Increments the current vault number and adds the vault to a list of allowed vaults.

```python
vaults['current_number'] += 1

vaults[vault_number, 'collateral_type'] = collateral_type
vaults[vault_number, 'minimum_collateralization'] = collateral_amount
vaults[vault_number, 'minimum_auction_time'] = collateral_amount
vaults[vault_number, 'cap'] = max_minted
vaults[vault_number, 'weight'] = weight

stability_rate[vault_number] = s_rate
```

#### Checks:

- Asserts the caller is the address specified in `vaults['OWNER']`

Returns the `vault_number` of the newly created vault type.


### remove_vault
Takes `vault_type: int`

Removes the specified vault from `vaults['list']`. This prevents new openings of the specified vault, but does not restrict actions of currently open vaults.

#### Checks:

- Asserts the caller is the address specified in `vaults['OWNER']`

Returns `None`.

### change_state
Takes `key: str, new_value: str, convert_to_decimal: bool = False`

Changes `vault[key]` to `new_value`.

#### Checks:

- Asserts the caller is the address specified in `vaults['OWNER']`
- Asserts `key` and `new_value` are both strings

Returns `new_value`.


### change_any_state
Takes `key: Any, new_value: Any`

Changes `vault[key]` to `new_value`.

#### Checks:

- Asserts the caller is the address specified in `vaults['OWNER']`

Returns `new_value`.


### change_stability_rate
Takes `key: int, new_value: float`

Changes `stability_rate[key]` to `new_value`.

#### Checks:

- Asserts the caller is the address specified in `vaults['OWNER']`

Returns `new_value`.


### get_collateralization_percent
Takes `cdp_number: int`

This is a getter and does not impact state in any way. It returns the collateralization percent of the requested vault.

#### Checks:

- Asserts the vault exists

Returns collateralization percent.


### assert_insufficent_collateral
Takes `cdp_number: int`

**Cannot be called**

#### Checks:

- Asserts the vault exists
- Asserts the vault is under-collateralized