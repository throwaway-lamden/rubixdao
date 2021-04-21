# taken from https://github.com/Lamden/amm/blob/master/lamden-version/test_refactor.py
import currency

I = importlib

# Enforceable interface
token_interface = [
    I.Func('transfer', args=('amount', 'to')),
    # I.Func('balance_of', args=('account')),
    I.Func('allowance', args=('owner', 'spender')),
    I.Func('approve', args=('amount', 'to')),
    I.Func('transfer_from', args=('amount', 'to', 'main_account'))
]

pairs = Hash()
prices = Hash(default_value=0)
lp_points = Hash(default_value=0)
reserves = Hash(default_value=[0, 0])

FEE_PERCENTAGE = 0.3 / 100


@export
def create_market(contract: str, currency_amount: float = 0, token_amount: float = 0):
    assert pairs[contract] is None, 'Market already exists!'
    assert currency_amount > 0 and token_amount > 0, 'Must provide currency amount and token amount!'

    token = I.import_module(contract)

    assert I.enforce_interface(token, token_interface), 'Invalid token interface!'

    currency.transfer_from(amount=currency_amount, to=ctx.this, main_account=ctx.caller)
    token.transfer_from(amount=token_amount, to=ctx.this, main_account=ctx.caller)

    prices[contract] = currency_amount / token_amount

    pairs[contract] = True

    # Mint 100 liquidity points
    lp_points[contract, ctx.caller] = 100
    lp_points[contract] = 100

    reserves[contract] = [currency_amount, token_amount]


@export
def liquidity_balance_of(contract: str, account: str):
    return lp_points[contract, account]


@export
def add_liquidity(contract: str, currency_amount: float = 0):
    assert pairs[contract] is True, 'Market does not exist!'

    assert currency_amount > 0

    token = I.import_module(contract)

    assert I.enforce_interface(token, token_interface), 'Invalid token interface!'

    # Determine the number of tokens required
    token_amount = currency_amount / prices[contract]

    # Transfer both tokens
    currency.transfer_from(amount=currency_amount, to=ctx.this, main_account=ctx.caller)
    token.transfer_from(amount=token_amount, to=ctx.this, main_account=ctx.caller)

    # Calculate the LP points to mint
    total_lp_points = lp_points[contract]
    currency_reserve, token_reserve = reserves[contract]

    points_per_currency = total_lp_points / currency_reserve
    lp_to_mint = points_per_currency * currency_amount

    # Update the LP poiunts
    lp_points[contract, ctx.caller] += lp_to_mint
    lp_points[contract] += lp_to_mint

    # Update the reserves
    reserves[contract] = [currency_reserve +
                          currency_amount, token_reserve + token_amount]


@export
def remove_liquidity(contract: str, amount: float = 0):
    assert pairs[contract] is True, 'Market does not exist!'

    assert amount > 0, 'Must be a positive LP point amount!'
    assert lp_points[contract, ctx.caller] >= amount, 'Not enough LP points to remove!'

    token = I.import_module(contract)

    assert I.enforce_interface(token, token_interface), 'Invalid token interface!'

    lp_percentage = amount / lp_points[contract]

    currency_reserve, token_reserve = reserves[contract]

    currency_amount = currency_reserve * lp_percentage
    token_amount = token_reserve * lp_percentage

    currency.transfer(to=ctx.caller, amount=currency_amount)
    token.transfer(to=ctx.caller, amount=token_amount)

    lp_points[contract, ctx.caller] -= amount
    lp_points[contract] -= amount

    assert lp_points[contract] > 1, 'Not enough remaining liquidity!'

    new_currency_reserve = currency_reserve - currency_amount
    new_token_reserve = token_reserve - token_amount

    assert new_currency_reserve > 0 and new_token_reserve > 0, 'Not enough remaining liquidity!'

    reserves[contract] = [new_currency_reserve, new_token_reserve]


@export
def transfer_liquidity(contract: str, to: str, amount: float):
    assert amount > 0, 'Must be a positive LP point amount!'
    assert lp_points[contract, ctx.caller] >= amount, 'Not enough LP points to transfer!'

    lp_points[contract, ctx.caller] -= amount
    lp_points[contract, to] += amount


@export
def approve_liquidity(contract: str, to: str, amount: float):
    assert amount > 0, 'Cannot send negative balances!'
    lp_points[contract, ctx.caller, to] += amount


@export
def transfer_liquidity_from(contract: str, to: str, main_account: str, amount: float):
    assert amount > 0, 'Cannot send negative balances!'

    assert lp_points[contract, main_account, ctx.caller] >= amount, 'Not enough coins approved to send! You have ' \
        '{} and are trying to spend {}'.format(
            lp_points[main_account, ctx.caller], amount)

    assert lp_points[contract, main_account] >= amount, 'Not enough coins to send!'

    lp_points[contract, main_account, ctx.caller] -= amount
    lp_points[contract, main_account] -= amount

    lp_points[contract, to] += amount

# Buy takes fee from the crypto being transferred in


@export
def buy(contract: str, currency_amount: float):
    assert pairs[contract] is not None, 'Market does not exist!'
    assert currency_amount > 0, 'Must provide currency amount!'

    token = I.import_module(contract)

    assert I.enforce_interface(token, token_interface), 'Invalid token interface!'

    currency_reserve, token_reserve = reserves[contract]
    k = currency_reserve * token_reserve

    new_currency_reserve = currency_reserve + currency_amount
    new_token_reserve = k / new_currency_reserve

    tokens_purchased = token_reserve - new_token_reserve

    fee = tokens_purchased * FEE_PERCENTAGE

    tokens_purchased -= fee
    new_token_reserve += fee

    assert tokens_purchased > 0, 'Token reserve error!'

    currency.transfer_from(amount=currency_amount, to=ctx.this, main_account=ctx.caller)
    token.transfer(amount=tokens_purchased, to=ctx.caller)

    reserves[contract] = [new_currency_reserve, new_token_reserve]
    prices[contract] = new_currency_reserve / new_token_reserve

# Sell takes fee from crypto being transferred out


@export
def sell(contract: str, token_amount: float):
    assert pairs[contract] is not None, 'Market does not exist!'
    assert token_amount > 0, 'Must provide currency amount and token amount!'

    token = I.import_module(contract)

    assert I.enforce_interface(token, token_interface), 'Invalid token interface!'

    currency_reserve, token_reserve = reserves[contract]
    k = currency_reserve * token_reserve

    new_token_reserve = token_reserve + token_amount

    new_currency_reserve = k / new_token_reserve

    currency_purchased = currency_reserve - new_currency_reserve  # MINUS FEE

    fee = currency_purchased * FEE_PERCENTAGE

    currency_purchased -= fee
    new_currency_reserve += fee

    assert currency_purchased > 0, 'Token reserve error!'

    token.transfer_from(amount=token_amount, to=ctx.this, main_account=ctx.caller)
    currency.transfer(amount=currency_purchased, to=ctx.caller)

    reserves[contract] = [new_currency_reserve, new_token_reserve]
    prices[contract] = new_currency_reserve / new_token_reserve
