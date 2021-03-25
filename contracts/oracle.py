current_price = Hash(default_value=0)

@export
def set_price(number: int, new_price: float):
    current_price[number] = new_price
    
@export
def get_price(number: int):
    return current_price[number]
