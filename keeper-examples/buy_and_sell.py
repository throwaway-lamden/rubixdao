import amm
import vault_contract
import oracle
import currency
import dai_contract

owner = Variable()
vault_list = Variable()
amm_reserves = ForeignHash(foreign_contract='amm', foreign_name='reserves')


@construct
def seed():
    owner.set(ctx.caller)
    vault_list.set([])


@export
def main():  # Amount compatibility can be added
    if amm_reserves['dai_contract'][0] / amm_reserves['dai_contract'][1] > 1:
        open_vault()

    elif amm_reserves['dai_contract'][0] / amm_reserves['dai_contract'][1] < 1:
        close_vault()

    else:
        check_collateral()  # Not yet implemented


@export
def withdraw(amount: float, is_tau: bool = False):
    assert_owner()

    if is_tau is True:
        # You can customize the 'to' as needed
        currency.transfer(amount=amount, to=owner.get())
    elif is_tau is False:  # Can be replaced with else
        dai_contract.transfer(amount=amount, to=owner.get())


@export
def close_specific_vault(v_id: int):
    assert_owner()

    v_list = vault_list.get()
    v_list.remove(v_id)
    vault_list.set(v_list)

    return vault_contract.close_vault(cdp_number=v_id)


@export
def close_all_vaults():
    assert_owner()

    for x in vault_list.get():
        vault_contract.close_vault(cdp_number=x)


def open_vault():
    # Asserts price after slippage allows for a profit
    assert internal_amm(amount=100, is_buy=False) > 100 / price, "No profit possible!"

    v_id = vault_contract.create_vault(
        vault_type=0, amount_of_dai=100, amount_of_collateral=200 / oracle.get_price(0))

    # Append new vault id to list # TODO: Make consistent with close_specific_vault
    vault_list.set(vault_list.get() + [v_id])

    return amm.sell(contract='dai_contract', amount=100)


def close_vault():
    # Asserts price after slippage allows for a profit
    assert internal_amm(amount=100 / oracle.get_price(0), is_buy=True) > 100, "No profit possible!"

    v_list = vault_list.get()
    v_id = v_list.pop(0)
    vault_list.set(v_list)

    amm.buy(contract='dai_contract', amount=(100 / oracle.get_price(0)) * 1.02)

    return vault_contract.close_vault(cdp_number=v_id)


def check_collateral():
    low_collateral = list()
    v_list = vault_list.get()
    for x in v_list():
        if vault_contract.get_collateralization_percent(x) < 1.6:
            low_collateral.append(x)

    for x in low_collateral:
        v_list.remove(x)
        vault_contract.close_vault(cdp_number=x)


def internal_amm(amount: float = 100, is_buy: bool = True):
    currency_reserve, token_reserve = amm_reserves['dai_contract']

    if is_buy is not True:
        currency_reserve, token_reserve = token_reserve, currency_reserve

    k = currency_reserve * token_reserve
    new_currency_reserve = currency_reserve + currency_amount
    new_token_reserve = k / new_currency_reserve

    tokens_purchased = token_reserve - new_token_reserve

    fee = tokens_purchased * 0.3 / 100

    return tokens_purchased - fee


def assert_owner():
    assert ctx.caller == owner.get(), 'Only operator can call!'

# def internal_sell(amount: float): #REPLACED WITH internal_amm
#    currency_reserve, token_reserve = amm_reserves['dai_contract']
#
#    k = currency_reserve * token_reserve
#    new_token_reserve = token_reserve + token_amount
#    new_currency_reserve = k / new_token_reserve
#
#    currency_purchased = currency_reserve - new_currency_reserve
#
#    fee = currency_purchased * 0.3 / 100
#
#    return currency_purchased - fee
