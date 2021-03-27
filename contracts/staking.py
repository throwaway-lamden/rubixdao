import dai_contract
import vaults

rate = Hash()
balances = Hash(default_value=0)

total_minted = Variable()
operator = Variable()

# 31540000 seconds per year
@construct
def seed():
    operator.set(ctx.caller)
    
    rate["start_time"] = now.seconds
    rate["rate"] = 1.000000001 # 3.2% interest yearly
    rate["start_price"] = 1
    
@export
def stake(amount: float):
    assert amount >= 0, "Stake amount must be positive!"
    dai_contract.transfer_from(to=ctx.this, amount=amount, main_account=ctx.caller)
    
    amount_minted = amount / get_price()
    total_minted.set(total_minted.get() + amount_minted)
    
    balances[ctx.caller] += amount_minted
    
    return amount_minted
    
@export   
def withdraw_stake(amount: float):
    assert amount >= 0, "Stake amount must be positive!"
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
    assert new_rate >= 1, "Cannot have negative staking!"
    
    current_price = get_price()
    
    rate["start_time"] = now.seconds
    rate["rate"] = new_rate
    rate["start_price"] = current_price
    
@export
def change_owner(new_owner: str):
    assert_owner()
    
    operator.set(new_owner)
   
@export 
def get_price():
    return rate["start_price"] * rate ** (now.seconds - rate["start_time"])
    
def assert_owner():
    assert ctx.caller == operator.get(), 'Only operator can call!'
    
