# Lamden MKR Contracts

## tad.py functions

### seed
Takes `owner: str`

**Cannot be called**

Sets the constants to their default value. As of now, you cannot pass arguments, and you have to manually modify the code.

The default values are as follows:
```python
total_supply.set(0)

operator.set(owner)

metadata['token_name'] = 'Lamden MKR'
metadata['token_symbol'] = 'lMKR'
metadata['token_logo_url'] = 'image.site'
metadata['operator'] = ctx.caller
```

### [LST-001](https://github.com/Lamden-Standards/LST001) and [LST-002](https://github.com/Lamden-Standards/LST002) compliant functions

Reference the linked repos for documentation on those functions.

### assert_owner

**Cannot be called**

Asserts that the caller is the operator.


#### Checks:

- Asserts the caller is the address stored in `operator`

### mint
Takes `amount: float`

Mints the amount specified and sends it to the caller.

Adds `amount` to `total_supply`.

#### Checks:

- Calls assert_owner
- Asserts that `amount` is positive

Returns `None`.

### burn
Takes `amount: float`

Transfers the amount specified from the caller and burns it.

Subtracts `amount` from `total_supply`.

#### Checks:

- Asserts that `amount` is positive
- Asserts that the balance of the caller is greater than `amount`

Returns `None`.
