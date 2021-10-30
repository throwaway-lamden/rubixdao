# RubixDAO Contracts

## stake.py functions

### seed
Takes `owner: str`

**Cannot be called**

Sets the constants to their default value. As of now, you cannot pass arguments, and you have to manually modify the code.

The default values are as follows:
```python
operator.set(ctx.caller)

rate['start_time'] = get_timestamp()
rate['rate'] = 1.0000000015469297  # interest per second
rate['start_price'] = 1

metadata['token_name'] = 'Staked tad'
metadata['token_symbol'] = 'stad'
metadata['token_logo_url'] = 'image.site'
metadata['operator'] = ctx.caller
total_minted.set(0)
```

### [LST-001](https://github.com/Lamden-Standards/LST001) and [LST-002](https://github.com/Lamden-Standards/LST002) compliant functions

Reference the linked repos for documentation on those functions.

### assert_owner

**Cannot be called**

Asserts that the caller is the operator.

#### Checks:

- Asserts the caller is the address stored in `operator`


### get_timestamp

**Cannot be called**

Returns current UTC timestamp.


### get_price

**Cannot be called**

Returns current price per stad.


### stake
Takes `amount: float`

Transfers the amount specified from the caller to the contract, and mints an equivalent amount of stad at a rate of `amount / get_price()`.

Adds the amount of stad minted to `total_minted`.

#### Checks:

- Asserts that `amount` is positive

Returns amount of stad minted.

### withdraw_stake
Takes `amount: float`

Burns the amount of stad specified. Transfers `total_minted / tad.balance_of(ctx.this)` to the caller, and calls `vault.mint_rewards()` to mint `(amount * price) - (total_minted / tad.balance_of(ctx.this)).

Subtracts `amount` from `total_minted`.

#### Checks:

- Asserts that `amount` is positive
- Asserts that the balance of the caller is greater than `amount`

Returns `None`.
