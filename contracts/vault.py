dai_contract = importlib.import_module('dai_contract')

vaults = Hash(default_value=0)
stability_rate = Hash(default_value=1)
cdp = Hash(default_value=0)
stability_pool = Hash(default_value=0)


@construct
def seed():
    vaults['OWNER'] = ctx.caller
    cdp['current_value'] = 0
    vaults['list'] = [0]
    vaults['current_number'] = 1

    vaults['oracle'] = 'oracle'  # dummy for testing purposes

    vaults[0, 'collateral_type'] = 'currency'
    vaults[0, 'minimum_collaterization'] = 1.5
    vaults[0, 'minimum_auction_time'] = 259200
    vaults[0, 'cap'] = 100000
    vaults[0, 'weight'] = 10

    stability_rate[0] = 1.1  # dummy for testing purposes


@export
def get_timestamp():
    # have to manually patch timezone since imports aren't on blockchain, this gives the utc timestamp for someone whose current locale is est
    td = now - datetime.datetime(1970, 1, 1, 0, 0, 0) + \
        datetime.timedelta(seconds=28800)
    return td.seconds


@export
def create_vault(vault_type: int, amount_of_dai: float,
                 amount_of_collateral: float):
    assert vault_type in vaults['list'], 'Not an available contract!'
    collateral = importlib.import_module(
        vaults[vault_type, 'collateral_type'])  # TODO: Add interface enforcement
    oracle = importlib.import_module(vaults['oracle'])

    price = oracle.get_price(vault_type)

    assert amount_of_dai > 0, 'Amount of DAI must be positive!'
    assert vaults[vault_type, 'total'] + amount_of_dai <= vaults[vault_type,
            'cap'], 'The allowance is not sufficent!'

    assert (amount_of_collateral * price) / \
        amount_of_dai >= vaults[vault_type,
                                'minimum_collaterization'], 'Not enough collateral!'

    cdp_number = cdp['current_value']
    cdp['current_value'] += 1

    cdp[cdp_number, 'owner'] = ctx.caller
    cdp[cdp_number, 'open'] = True

    cdp[cdp_number, 'collateral_type'] = vaults[vault_type, 'collateral_type']
    cdp[cdp_number, 'vault_type'] = vault_type
    cdp[cdp_number, 'dai'] = amount_of_dai
    cdp[cdp_number, 'collateral_amount'] = amount_of_collateral
    cdp[cdp_number, 'time'] = get_timestamp()

    collateral.approve(amount=amount_of_collateral, to=ctx.this)
    collateral.transfer_from(amount=amount_of_collateral,
                             to=ctx.this, main_account=ctx.caller)

    dai_contract.mint(amount=amount_of_dai)
    dai_contract.transfer(amount=amount_of_dai, to=ctx.caller)

    vaults[vault_type, 'issued'] += amount_of_dai
    vaults[vault_type, 'total'] += amount_of_dai

    return cdp_number


@export
def close_vault(cdp_number: int):
    assert cdp[cdp_number, 'owner'] == ctx.caller, 'Not the owner!'
    assert cdp[cdp_number, 'open'] == True, 'Vault has already been closed!'

    collateral = importlib.import_module(
        vaults[cdp[cdp_number, 'vault_type'], 'collateral_type'])

    stability_ratio = vaults[cdp[cdp_number, 'vault_type'], 'issued'] / \
        vaults[cdp[cdp_number, 'vault_type'], 'total']
    redemption_cost = cdp[cdp_number, 'dai'] * stability_ratio
    fee = redemption_cost * \
        (stability_rate[cdp[cdp_number, 'vault_type']] **
         (get_timestamp() - cdp[cdp_number, 'time'])) - redemption_cost

    amount = redemption_cost + fee
    dai_contract.transfer_from(
        amount=amount, to=ctx.this, main_account=ctx.caller)
    dai_contract.burn(amount=redemption_cost)

    stability_pool[cdp[cdp_number, 'collateral_type']] += fee

    vaults[cdp[cdp_number, 'vault_type'], 'issued'] -= cdp[cdp_number, 'dai']
    # This is only different if the ratio is different
    vaults[cdp[cdp_number, 'vault_type'], 'total'] -= redemption_cost

    cdp[cdp_number, 'open'] = False

    # Return collateral
    collateral.transfer(
        amount=cdp[cdp_number, 'collateral_amount'], to=ctx.caller)

    return amount


@export
def fast_force_close_vault(cdp_number: int):
    assert cdp[cdp_number, 'open'] is True, 'Vault has already been closed!'

    collateral = importlib.import_module(
        vaults[cdp[cdp_number, 'vault_type'], 'collateral_type'])
    oracle = importlib.import_module(vaults['oracle'])

    stability_ratio = vaults['issued'] / vaults['total']
    redemption_cost_without_fee = cdp[cdp_number,
                                      'dai'] * stability_ratio
    redemption_cost = redemption_cost_without_fee * 1.1
    fee = redemption_cost - redemption_cost * \
        (stability_rate[cdp[cdp_number, 'vault_type']]
         ** (get_timestamp() - cdp[cdp_number, time]))
    redemption_cost += fee

    amount_of_collateral = cdp[cdp_number, 'collateral_amount']
    collateral_type = cdp[cdp_number, 'collateral_type']
    collateral_percent = (amount_of_collateral * price) / \
        (redemption_cost + fee)

    price = oracle.get_price(cdp[cdp_number, 'vault_type'])

    # TODO: Make this not a one liner
    assert cdp[cdp_number, 'collateral_amount'] * price / cdp[cdp_number,
                                                              'dai'] < vaults['minimum_collaterization'][cdp[cdp_number, 'vault_type']], 'Vault above minimum collateralization!'

    if collateral_percent >= 1.03:
        dai_contract.transfer_from(
            amount=redemption_cost, to=ctx.this, main_account=ctx.caller)
        dai_contract.burn(amount=redemption_cost_without_fee)

        amount = (1 / price) * (redemption_cost_without_fee) * 1.03

        collateral.transfer(amount=amount, to=ctx.caller)
        collateral.transfer(amount=collateral_amount -
                            (amount * 1.1), to=cdp[number, 'owner'])

        vaults[cdp[cdp_number, 'vault_type'],
               'issued'] -= cdp[cdp_number, 'dai']
        vaults[cdp[cdp_number, 'vault_type'], 'total'] -= redemption_cost

    else:
        redemption_cost, redemption_cost_without_fee = redemption_cost * \
            (collateral_percent / 1.03), redemption_cost_without_fee * \
            (collateral_percent / 1.03)

        dai_contract.transfer_from(
            amount=redemption_cost + fee, to=ctx.this, main_account=ctx.caller)
        dai_contract.burn(amount=redemption_cost)

        amount = (1 / price) * (redemption_cost_without_fee) * \
            1.03  # TODO: Double check math

        # TODO: Add an assert later
        collateral.transfer(amount=amount, to=ctx.caller)

        vaults[cdp[cdp_number, 'vault_type'], 'issued'] -= cdp[number, 'dai']
        vaults[cdp[cdp_number, 'vault_type'], 'total'] -= redemption_cost

    stability_pool[cdp[number, 'collateral_type']
                   ] += redemption_cost - redemption_cost_without_fee

    return amount


@export
def open_force_close_auction(cdp_number: int):
    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'
    assert cdp[cdp_number, 'auction',
               'open'] != True, 'Auction is already taking place!'
    assert cdp[cdp_number, 'open'] is True, 'Vault has already been closed!'

    # This contract may only be bid on, and not closed
    cdp[cdp_number, 'open'] = False
    cdp[cdp_number, 'auction', 'open'] = True

    cdp[cdp_number, 'auction', 'highest_bidder'] = ctx.caller
    cdp[cdp_number, 'auction', 'top_bid'] = 0.0

    cdp[cdp_number, 'auction', 'time'] = get_timestamp()

    return True


@export
def bid_on_force_close(cdp_number: int, amount: float):
    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'
    assert cdp[cdp_number, 'auction',
                   'open'] is True, 'Auction is not open!'
    assert amount > cdp[cdp_number, 'auction',
                        'top_bid'], 'There is already a higher bid!'

    if cdp[cdp_number, 'auction', ctx.caller, 'bid'] is not None:
        dai_contract.transfer_from(
            amount=amount - cdp[cdp_number, 'auction', ctx.caller, 'bid'],
            to=ctx.this, main_account=ctx.caller)

    else:
        dai_contract.transfer_from(
            amount=amount, to=ctx.this, main_account=ctx.caller)

    cdp[cdp_number, 'auction', 'highest_bidder'] = ctx.caller
    cdp[cdp_number, 'auction', 'top_bid'] = amount
    cdp[cdp_number, 'auction', ctx.caller, 'bid'] = amount

    return True


@export
def settle_force_close(cdp_number: int):
    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'
    assert cdp[cdp_number, 'auction', 'open'] is True, 'Auction is not open!'

    assert get_timestamp() - cdp[cdp_number, 'auction', 'time'] > vaults[cdp[cdp_number, 'vault_type'],
           'minimum_auction_time'], 'Auction is still open!'

    collateral = importlib.import_module(
        vaults[cdp[cdp_number, 'vault_type'], 'collateral_type'])

    cdp[cdp_number, 'auction', 'settled'] = True
    cdp[cdp_number, 'open'] = False
    cdp[cdp_number, 'auction', 'open'] = False

    cdp[cdp_number, 'auction', cdp[cdp_number,
                                   'auction', 'highest_bidder'], 'bid'] = 0

    fee = cdp[cdp_number, 'auction', 'top_bid'] * 0.1
    collateral.transfer_from(
        amount=cdp[cdp_number, 'collateral_amount'], to=ctx.caller, main_account=ctx.this)
    dai_contract.burn(amount=cdp[cdp_number, 'auction', 'top_bid'] - fee)

    stability_pool[cdp[cdp_number, 'collateral_type']] += fee

    vaults[cdp[cdp_number, 'vault_type'], 'issued'] -= cdp[cdp_number, 'dai']
    vaults[cdp[cdp_number, 'vault_type'],
           'total'] -= cdp[cdp_number, 'auction', 'top_bid'] - fee # Fee is technically not burned

    return cdp[cdp_number, 'auction', 'highest_bidder'], cdp[cdp_number,
                                                             'auction', 'top_bid']


@export
def claim_unwon_bid(cdp_number: int):
    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'
    assert cdp[cdp_number, 'auction',
               'settled'] is True, 'Auction is still open or not opened!'

    dai_contract.transfer(
        to=ctx.caller, amount=cdp[cdp_number, 'auction', ctx.caller, 'bid'])
    cdp[cdp_number, 'auction', ctx.caller, 'bid'] = 0

    return True


@export
def sync_stability_pool(vault_type: int):
    assert vault_type in vaults['list'], 'Not an available contract!'

    default_amount = vaults[vault_type, 'total'] - vaults[vault_type, 'issued']

    if default_amount > stability_pool[vault_type]:
        vaults[vault_type, 'issued'] += stability_pool[vault_type]
        stability_pool[vault_type] = 0

        # Return new ratio
        return vaults[vault_type, 'issued'] / vaults[vault_type, 'total']

    else:  # This also applies to negatives, although those situations are unlikely
        vaults[vault_type, 'issued'] = vaults[vault_type, 'total']
        stability_pool[vault_type] -= default_amount

        return 1.0  # The ratio is perfectly equal


@export
def export_rewards(vault_type: int, amount: float):
    # TODO: Change DSR to something else in future
    assert vaults[vault_type, 'DSR', 'owner'] == ctx.caller, 'Not the owner!'
    assert stability_pool[vault_type] >= amount, 'Not enough DAI in stability pool to export!'

    stability_pool[vault_type] -= amount
    dai_contract.transfer(to=ctx.caller, amount=amount)

    return True


@export
def mint_rewards(amount: float):  # TODO: MAKE SURE MATH CHECKS OUT
    # TODO: Change DSR to something else in future
    assert vaults['mint', 'DSR', 'owner'] == ctx.caller, 'Not the owner!'
    assert amount > 0, 'Cannot mint negative amount!'

    dai_contract.mint(amount=amount)
    dai_contract.transfer(to=ctx.caller, amount=amount)

    total_weight = 0
    total_funds = amount

    for vault_type in vaults['list']:
        total_weight += vaults[vault_type, 'weight']

    # To make the contract more robust, and to prevent floating point errors
    for vault_type in vaults['list']:
        funds_transferred = decimal(
            vaults[vault_type, 'weight'] / total_weight) * total_funds
        vaults[vault_type, 'total'] += funds_transferred

        total_funds -= funds_transferred
        total_weight -= vaults[vault_type, 'weight']

    return True


@export
def sync_burn(vault_type: int, amount: float):
    assert vault_type in vaults['list'], 'Not an available contract!'

    dai_contract.transfer_from(to=ctx.this, amount=amount)
    dai_contract.burn(amount=amount)

    vaults[vault_type, 'total'] -= amount

    return vaults[vault_type, 'total']


@export
def add_vault(collateral_type: str, collateral_amount: float, auction_time: float,
              max_minted: float, s_rate: float, weight: float):
    assert vaults['OWNER'] == ctx.caller, 'Not the owner!'

    vault_number = vaults['current_number']
    vaults['list'].append(vault_number)
    vaults['current_number'] += 1

    vaults[vault_number, 'collateral_type'] = collateral_type
    vaults[vault_number, 'minimum_collaterization'] = collateral_amount
    vaults[vault_number, 'minimum_auction_time'] = collateral_amount
    vaults[vault_number, 'cap'] = max_minted
    vaults[vault_number, 'weight'] = weight

    stability_rate[vault_number] = s_rate

    return vault_number


@export
def remove_vault(vault_type: int):
    assert vaults['OWNER'] == ctx.caller, 'Not the owner!'
    vaults['list'].remove(vault_type)


@export
def change_state(key: str, new_value: str, convert_to_decimal: bool = False):
    assert vaults['OWNER'] == ctx.caller, 'Not the owner!'
    assert type(key) == str, 'Invalid type for key'
    assert type(new_value) == str, 'Invalid type for new value'

    if convert_to_decimal:
        new_value = decimal(new_value)
    vaults[key] = new_value

    return new_value


@export
def change_any_state(key: Any, new_value: Any):
    assert vaults['OWNER'] == ctx.caller, 'Not the owner!'

    vaults[key] = new_value

    return new_value


@export
def change_stability_rate(key: int, new_value: float):  # don't add type checks
    assert vaults['OWNER'] == ctx.caller, 'Not the owner!'

    stability_rate[key] = new_value

    return new_value


@export
def get_collateralization_percent(cdp_number: int):
    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'
    # TODO: Change this from a one-liner to proper function
    oracle = importlib.import_module(vaults['oracle'])

    return cdp[cdp_number, 'collateral_amount'] * oracle.get_price(cdp[cdp_number, 'vault_type']) / cdp[cdp_number, 'dai']
    # code to check if minimum is met would be
    # assert cdp[cdp_number, 'collateral_amount'] >= vaults[cdp[cdp_number, 'collateral_type'], 'minimum_collaterization']
