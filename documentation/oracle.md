# Lamden MKR Contracts

## oracle.py functions

### seed

**Cannot be called**

Sets the constants to their default value. As of now, you cannot pass arguments, and you have to manually modify the code.

The default values are as follows:
```python
operator.set(ctx.caller)
```


### set_price
Takes `number: int, new_price: float`

Sets `current_price[number]` to `new_price`.

#### Checks: 

- Asserts that `new_price` is positive 
- Asserts that the caller is the address specified in `operator`

Returns `None`.


### get_price
Takes `number: int`

This function does not modify state. 

This function returns the current price for the specified vault.

#### Checks: 

- N/A

Returns `current_price[number]`.
