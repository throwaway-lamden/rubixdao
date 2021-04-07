current_price = Hash(default_value=0)
operator = Variable()

@construct
def seed():
    operator.set(ctx.caller)
    

@export
def set_price(number: int, new_price: float):
    assert new_price >= 0, 'Cannot set negative prices!'
    assert ctx.caller == operator.get(), 'You do not have permission to set the price.'
    
    current_price[number] = new_price


@export
def get_price(number: int):
    return current_price[number]
