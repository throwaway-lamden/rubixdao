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
    
    cdp[cdp_number, owner] = ctx.caller
    
    cdp[cdp_number, collateral_type] = vault_type
    cdp[cdp_number, dai] = amount_of_dai
    cdp[cdp_number, collateral_amount] = amount_of_collateral
    cdp[cdp_number, time] = now.seconds #TODO: make sure this works
    
    importlib.transfer_from(amount=amount_of_collateral, to=ctx.this, main_account=ctx.caller)
    
    dai_contract.mint(amount=amount_of_dai)
    dai_contract.transfer(amount=amount_of_dai, to=ctx.caller)

    vaults[vault_type, "issued"] += amount_of_dai
    vaults[vault_type, "total"] += amount_of_dai
    
    return cdp_number
    
@export
def close_vault(number: int):
    assert cdp[cdp_number, owner] == ctx.caller, "Not the owner!"
    
    stability_ratio = vaults["issued"] / vaults["total"]
    redemption_cost = cdp[number, "amount_of_dai"] * stability_ratio
    fee = redemption_cost * (stability_rate * (now.seconds - cdp[number, "time"]))
    
    dai_contract.transfer_from(amount=redemption_cost + fee, to=ctx.this, main_account=ctx.caller)
    dai_contract.burn(amount=redemption_cost)
    
    stability_pool[cdp[number, "collateral_type"]] += fee
    
    vaults[vault_type, "issued"] -= cdp[number, "dai"]
    vaults[vault_type, "total"] -= redemption_cost
    
    importlib.transfer(amount=cdp[cdp_number, "collateral_amount"], to=ctx.caller)
    
@export
def fast_force_close_vault(number: int):
    stability_ratio = vaults["issued"] / vaults["total"]
    redemption_cost_without_fee = cdp[number, "amount_of_dai"] * stability_ratio 
    redemption_cost = redemption_cost_without_fee * 1.1
    fee = redemption_cost * (stability_rate * (now.seconds - cdp[number, time]))
    
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
        redemption_cost, redemption_cost_without_fee = redemption_cost * collateral_percent / 1.03, redemption_cost_without_fee * collateral_percent / 1.03
        
        dai_contract.transfer_from(amount=redemption_cost + fee, to=ctx.this, main_account=ctx.caller)
        dai_contract.burn(amount=redemption_cost)
        
        amount = (1 / price) * (redemption_cost_without_fee) * 1.03

        importlib.transfer(amount=amount, to=ctx.caller) # TODO: Add an assert later

        vaults[vault_type, "issued"] -= cdp[number, "dai"]
        vaults[vault_type, "total"] -= redemption_cost
        
    stability_pool[cdp[number, "collateral_type"]] += redemption_cost - redemption_cost_without_fee
    
@export
def open_force_close_auction():
    
@export
def bid_on_force_close():
    
@export
def change_state():
    
