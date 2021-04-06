balances = Hash(default_value=0)
metadata = Hash()

operator = Variable()
total_supply = Variable()


@construct
def seed(owner: str):
    total_supply.set(0)

    operator.set(owner)

    metadata['token_name'] = 'Lamden MKR'
    metadata['token_symbol'] = 'lMKR'
    metadata['token_logo_url'] = 'image.site'
    metadata['operator'] = ctx.caller


@export
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send non-positive balances!'

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
    assert amount > 0, 'Cannot send non-positive balances!'
    sender = ctx.caller
    
    balances[sender, to] += amount
    return balances[sender, to]


@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send non-positive balances!'

    sender = ctx.caller

    assert balances[main_account] >= amount, 'Not enough coins to send!'
    assert balances[main_account, sender] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
        .format(balances[main_account, sender], amount)

    balances[main_account, sender] -= amount
    balances[main_account] -= amount

    balances[to] += amount


@export
def mint(amount: float):
    assert_owner()

    assert amount > 0, 'Cannot mint non-positive balances!'

    sender = ctx.caller
    balances[sender] += amount

    total = total_supply.get() + amount
    total_supply.set(total)


@export
def burn(amount: float):
    assert amount > 0, 'Cannot burn non-positive balances!'

    sender = ctx.caller

    assert balances[sender] >= amount, 'Not enough coins to burn!'

    balances[sender] -= amount

    total = total_supply.get() - amount
    total_supply.set(total)


@export
def get_total_supply():
    return total_supply.get()


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
