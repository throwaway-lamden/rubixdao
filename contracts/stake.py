tad_contract = importlib.import_module('tad_contract')
vault_contract = importlib.import_module('vault_contract')

rate = Hash()

balances = Hash(default_value=0)
metadata = Hash()

total_minted = Variable()
operator = Variable()

temporary_var = Variable()


@construct
def seed():
    operator.set(ctx.caller)

    rate['start_time'] = get_timestamp()
    rate['rate'] = 1.0000000015469297  # interest per second
    rate['start_price'] = 1

    metadata['token_name'] = 'Staked tad'
    metadata['token_symbol'] = 'stad'
    metadata['token_logo_url'] = 'image.site'
    metadata['operator'] = ctx.caller
    total_minted.set(0)


@export
def get_timestamp():
    # https://developers.lamden.io/docs/smart-contracts/datetime-module/
    td = now - datetime.datetime(1970, 1, 1, 0, 0, 0)
    return fix_decimal(td.seconds / 1000000)


@export
def stake(amount: float):
    assert amount > 0, 'Stake amount must be positive!'
    tad_contract.transfer_from(
        to=ctx.this, amount=amount, main_account=ctx.caller)

    amount_minted = amount / get_price()
    total = total_minted.get() + amount_minted
    total_minted.set(total)

    balances[ctx.caller] += amount_minted

    return amount_minted


@export
def withdraw_stake(amount: float):
    assert amount > 0, 'Stake amount must be positive!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to withdraw!'

    balances[ctx.caller] -= amount

    current_price = get_price()
    return_amount = current_price * amount

    supply = total_minted.get()
    current_average = fix_decimal(supply / tad_contract.balance_of(ctx.this))
    transfer_away_amount = amount * current_average

    total_minted.set(supply - amount)
    if return_amount - transfer_away_amount > 0:
        vault_contract.mint_rewards(
            amount=return_amount - transfer_away_amount)

    tad_contract.transfer(amount=return_amount, to=ctx.caller)

    return return_amount


@export
def change_rate(new_rate: float):  # takes yearly interest as decimal
    assert_owner()
    assert new_rate >= 0, 'Cannot have negative staking!'

    current_price = get_price()

    rate['start_time'] = get_timestamp()
    rate['rate'] = new_rate  # interest per second
    rate['start_price'] = current_price


@export
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'

    sender = ctx.caller

    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount
    balances[to] += amount


@export
def balance_of(account: str):
    return balances[account]


@export
def allowance(owner: str, spender: str):
    return balances[owner, spender]


@export
def approve(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    sender = ctx.caller
    assert balances[sender] >= amount, 'Cannot approve balance that exceeds total balance!'
    balances[sender, to] += amount
    return balances[sender, to]


@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send negative balances!'

    sender = ctx.caller

    assert balances[main_account] >= amount, 'Not enough coins to send!'
    assert balances[main_account, sender] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
        .format(balances[main_account, sender], amount)

    balances[main_account, sender] -= amount
    balances[main_account] -= amount

    balances[to] += amount


@export
def get_price():
    return rate['start_price'] * rate['rate'] ** (
        get_timestamp() - rate['start_time'])


@export
def change_metadata(key: str, value: Any):
    assert ctx.caller == metadata['operator'], 'Only operator can set metadata!'
    metadata[key] = value


@export
def change_owner(new_owner: str):
    assert_owner()
    operator.set(new_owner)


def assert_owner():
    assert ctx.caller == operator.get(), 'Only operator can call!'
    
    
def fix_decimal(old_decimal: float):
    temporary_var.set(old_decimal)
    new_decimal = temporary_var.get()
    
    return new_decimal
