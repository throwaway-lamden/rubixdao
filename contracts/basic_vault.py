import oracle
import dai_contract
vaults = Hash(default_value=0)
cdp = Hash()
stability_pool = Hash()

@export
def create_vault(vault_type: int, amount_of_dai: float, amount_of_collateral: float):
    assert vault_type in vaults["list"], "Not an available contract!"
    
    IMPORTLIB STUFF with this
    vaults["contract"][vault_type] 
    
    #vault_name = vaults["list"][vault_type] #This should error out if out of range, should still do sanity checks though #Probably not needed
    
    price = oracle.get_price(vault_type)
    
    assert (amount_of_collateral * price) / amount_of_dai > vaults["minimum_collaterization"][vault_type], "Not enough collateral!"
    
    cdp_number = cdp[current_value] 
    cdp[current_value] += 1
    
    cdp[cdp_number, "owner"] = ctx.caller
    cdp[cdp_number, "open"] = True
    
    cdp[cdp_number, "collateral_type"] = vault_type
    cdp[cdp_number, "dai"] = amount_of_dai
    cdp[cdp_number, "collateral_amount"] = amount_of_collateral
    cdp[cdp_number, "time"] = now.seconds #TODO: make sure this works
    
    importlib.transfer_from(amount=amount_of_collateral, to=ctx.this, main_account=ctx.caller)
    
    dai_contract.mint(amount=amount_of_dai)
    dai_contract.transfer(amount=amount_of_dai, to=ctx.caller)

    vaults[vault_type, "issued"] += amount_of_dai
    vaults[vault_type, "total"] += amount_of_dai
    
    return cdp_number
    
@export
def close_vault(cdp_number: int):
    assert cdp[cdp_number, "owner"] == ctx.caller, "Not the owner!"
    assert cdp[cdp_number, "open"] is True, "Vault has already been closed!"
    
    stability_ratio = vaults["issued"] / vaults["total"]
    redemption_cost = cdp[number, "amount_of_dai"] * stability_ratio
    fee = redemption_cost * (stability_rate * (now.seconds - cdp[number, "time"]))
    
    dai_contract.transfer_from(amount=redemption_cost + fee, to=ctx.this, main_account=ctx.caller)
    dai_contract.burn(amount=redemption_cost)
    
    stability_pool[cdp[number, "collateral_type"]] += fee
    
    vaults[vault_type, "issued"] -= cdp[number, "dai"]
    vaults[vault_type, "total"] -= redemption_cost
    
    cdp[cdp_number, "open"] = False
    
    importlib.transfer(amount=cdp[cdp_number, "collateral_amount"], to=ctx.caller)
    
@export
def fast_force_close_vault(cdp_number: int):
    assert cdp[cdp_number, "open"] is True, "Vault has already been closed!"
    
    stability_ratio = vaults["issued"] / vaults["total"]
    redemption_cost_without_fee = cdp[number, "amount_of_dai"] * stability_ratio 
    redemption_cost = redemption_cost_without_fee * 1.1
    fee = redemption_cost * (stability_rate * (now.seconds - cdp[number, time]))
    redemption_cost += fee
    
    amount_of_collateral = cdp[number, "collateral_amount"]
    collateral_type = cdp[number, "collateral_type"]
    collateral_percent = (amount_of_collateral * price) / (redemption_cost + fee)
    
    price = oracle.get_price(vault_type)
    
    assert cdp[number, "collateral_amount"] < vaults["minimum_collaterization"][vault_type], "Vault above minimum collateralization!"
    
    if collateral_percent >= 1.03:
        dai_contract.transfer_from(amount=redemption_cost, to=ctx.this, main_account=ctx.caller)
        dai_contract.burn(amount=redemption_cost_without_fee)
        
        amount = (1 / price) * (redemption_cost_without_fee) * 1.03

        importlib.transfer(amount=amount, to=ctx.caller)
        importlib.transfer(amount=collateral_amount - (amount * 1.1), to=cdp[number, "owner"])
    
        vaults[vault_type, "issued"] -= cdp[number, "dai"]
        vaults[vault_type, "total"] -= redemption_cost

    else:
        redemption_cost, redemption_cost_without_fee = redemption_cost * (collateral_percent / 1.03), redemption_cost_without_fee * (collateral_percent / 1.03)
        
        dai_contract.transfer_from(amount=redemption_cost + fee, to=ctx.this, main_account=ctx.caller)
        dai_contract.burn(amount=redemption_cost)
        
        amount = (1 / price) * (redemption_cost_without_fee) * 1.03

        importlib.transfer(amount=amount, to=ctx.caller) # TODO: Add an assert later

        vaults[vault_type, "issued"] -= cdp[number, "dai"]
        vaults[vault_type, "total"] -= redemption_cost
        
    stability_pool[cdp[number, "collateral_type"]] += redemption_cost - redemption_cost_without_fee
    
    return amount
    
@export
def open_force_close_auction(cdp_number: int):
    assert cdp[cdp_number, "open"] is True, "Vault has already been closed!"
    assert cdp[cdp_number, "auction", "open"] is False, "Auction is already taking place!" # May not work
    
    cdp[cdp_number, "open"] = False # This contract may only be bid on, and not closed
    cdp[cdp_number, "auction", "open"] = True
    
    cdp[cdp_number, "auction", "highest_bidder"] = ctx.caller
    cdp[cdp_number, "auction", "top_bid"] = 0.0
    cdp[cdp_number, "auction", "time"] = now.seconds #TODO: make sure this works
    
    return True
    
@export
def bid_on_force_close(cdp_number: int, amount: float):
    assert cdp[cdp_number, "open"] is True, "Vault has already been closed!"
    assert cdp[cdp_number, "auction", "open"] is True, "Auction is not open!" # May not work
    assert amount > cdp[cdp_number, "auction", "top_bid"], "There is already a higher bid!"
    
    if cdp[cdp_number, "auction", ctx.caller, "bid"] is not None:
        dai_contract.transfer_from(amount=amount - cdp[cdp_number, "auction", ctx.caller, "bid"], to=ctx.this, main_account=ctx.caller)
        
    else:
        dai_contract.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)
    
    cdp[cdp_number, "auction", "highest_bidder"] = ctx.caller
    cdp[cdp_number, "auction", "top_bid"] = amount
    cdp[cdp_number, "auction", ctx.caller, "bid"] = amount
    
    return True
    
@export
def settle_force_close(cdp_number: int):
    assert cdp[cdp_number, "open"] is True, "Vault has already been closed!"
    assert cdp[cdp_number, "auction", "open"] is True, "Auction is not open!" 
    
    assert now.seconds - cdp[cdp_number, "auction", "time"] > vaults[vault_type, "minimum_auction_time"], "Auction is still open!"
    
    cdp[cdp_number, "auction", "settled"] = True
    cdp[cdp_number, "open"] = False
    cdp[cdp_number, "auction", "open"] = False
    
    cdp[cdp_number, "auction", cdp[cdp_number, "auction", "highest_bidder"], "bid"] = 0
    
    fee = cdp[cdp_number, "dai"] * 0.1
    dai_contract.transfer_from(amount=cdp[cdp_number, "dai"] - fee, to=ctx.caller)
    
    stability_pool[cdp[number, "collateral_type"]] += fee
    
    vaults[vault_type, "issued"] -= cdp[number, "dai"]
    vaults[vault_type, "total"] -= cdp[cdp_number, "auction", "top_bid"]
    
    return cdp[cdp_number, "auction", "highest_bidder"], cdp[cdp_number, "auction", "top_bid"]
 
@export
def claim_unwon_bid(cdp_number: int):
    assert cdp[cdp_number, "auction", "settled"] is True, "Auction is not over!"
    
    importlib
    collateral.transfer(to=ctx.caller, amount=cdp[cdp_number, "auction", ctx.caller, "bid"])
    cdp[cdp_number, "auction", ctx.caller, "bid"] = 0
    
    return True
    
@export
def sync_stability_pool(vault_type: int):
    assert vault_type in vaults["list"], "Not an available contract!"
    
    default_amount = vaults[vault_type, "total"] - vaults[vault_type, "issued"]
    
    if default_amount > stability_pool[vault_type]:
        vaults[vault_type, "issued"] += stability_pool[vault_type]
        stability_pool[vault_type] = 0
        
        return vaults[vault_type, "issued"] / vaults[vault_type, "total"] # Return new ratio
        
    else: # This also applies to negatives, although those situations are unlikely
        vaults[vault_type, "issued"] = vaults[vault_type, "total"]
        stability_pool[vault_type] -= default_amount
        
        return 1.0 # The ratio is perfectly equal
        
@export
def sync_burn():

@export
def change_state(key: str, new_value: str, convert_to_decimal: bool=False):
    assert state["OWNER"] == ctx.caller, "Not the owner!"
    
    if convert_to_decimal:
        new_value = decimal(new_value)
        
    state[key] = new_value
        
    return new_value
    
@export
def change_any_state(key: Any, new_value: Any):
    assert state["OWNER"] == ctx.caller, "Not the owner!"
    
    state[key] = new_value
        
    return new_value
    
