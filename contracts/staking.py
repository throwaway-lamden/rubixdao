import dai_contract
import vault_contract

rate = Hash()

balances = Hash(default_value=0)
metadata = Hash()

total_minted = Variable()
operator = Variable()

# 31540000 seconds per year


@construct
def seed():
    operator.set(ctx.caller)

    rate['start_time'] = get_timestamp()
    yearly_rate = 0.05  # yearly interest
    rate['rate'] = 1 + yearly_rate / 31540000  # interest per second
    rate['start_price'] = 1

    metadata['token_name'] = 'Staked DAI'
    metadata['token_symbol'] = 'sDAI'
    metadata['token_logo_url'] = 'image.site'
    metadata['operator'] = ctx.caller


@export
def get_timestamp():
    td = now - datetime.datetime(1970, 1, 1, 0, 0, 0) + datetime.timedelta(seconds=28800) # have to manually patch timezone since imports aren't on blockchain, this gives the utc timestamp for someone whose current locale is est
    return td.seconds


@export
def stake(amount: float):
    assert amount >= 0, 'Stake amount must be positive!'
    dai_contract.transfer_from(
        to=ctx.this, amount=amount, main_account=ctx.caller)

    amount_minted = amount / get_price()
    total_minted.set(total_minted.get() + amount_minted)

    balances[ctx.caller] += amount_minted

    return amount_minted


@export
def withdraw_stake(amount: float):
    assert amount >= 0, 'Stake amount must be positive!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to send!'

    current_price = get_price()
    return_amount = current_price * amount

    supply = total_minted.get()
    current_average = supply / dai_contract.balance_of(ctx.this)
    transfer_away_amount = amount * current_average

    total_minted.set(supply - amount)

    dai_contract.mint_rewards(amount=return_amount - transfer_away_amount)
    dai_contract.transfer(amount=return_amount, to=ctx.caller)

    return return_amount


@export
def change_rate(new_rate: float):
    assert_owner()
    assert new_rate >= 1, 'Cannot have negative staking!'

    current_price = get_price()

    rate['start_time'] = get_timestamp()
    rate['rate'] = new_rate
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
    balances[sender, to] += amount
    return balances[sender, to]


@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send negative balances!'

    sender = ctx.caller

    assert balances[main_account, sender] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
        .format(balances[main_account, sender], amount)
    assert balances[main_account] >= amount, 'Not enough coins to send!'

    balances[main_account, sender] -= amount
    balances[main_account] -= amount

    balances[to] += amount


@export
def get_price():
    return rate['start_price'] * rate ** (get_timestamp() - rate['start_time'])


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
