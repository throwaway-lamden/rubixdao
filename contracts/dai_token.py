balances = Hash(default_value=0)
operator = Variable()

@construct
def seed(vk: str, owner: str):
    balances[vk] = 288_090_567
    operator.set(owner)

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
def mint(amount: float):
    assert_owner()
    
    assert amount > 0, 'Cannot mint negative balances!'

    sender = ctx.caller
    balances[sender] += amount
    
@export
def burn(amount: float):
    assert amount > 0, 'Cannot burn negative balances!'

    sender = ctx.caller

    assert balances[sender] >= amount, 'Not enough coins to burn!'
    
    balances[sender] -= amount
    
@export
def change_owner(new_owner: str):
    assert_owner()
    
    operator.set(new_owner)
    
def assert_owner():
    assert ctx.caller == operator.get(), 'Only operator can call!'
