tad_contract = importlib.import_module('tad_contract')

vaults = Hash(default_value=0)
stability_rate = Hash(default_value=1)
cdp = Hash(default_value=0)
stability_pool = Hash(default_value=0)

temporary_var = Variable()

@construct
def seed():
    vaults['OWNER'] = ctx.caller
    cdp['current_value'] = 0
    vaults['list'] = [0]
    vaults['current_number'] = 1

    vaults['oracle'] = 'oracle'  # dummy for testing purposes

    vaults[0, 'collateral_type'] = 'currency'
    vaults[0, 'minimum_collateralization'] = 1.5
    vaults[0, 'minimum_auction_time'] = 259.2
    vaults[0, 'cap'] = 100000
    vaults[0, 'weight'] = 10

    stability_rate[0] = 1.1  # default value, change on deployment


@export
def get_timestamp():
    # https://developers.lamden.io/docs/smart-contracts/datetime-module/
    td = now - datetime.datetime(1970, 1, 1, 0, 0, 0)
    return fix_decimal(td.seconds / 1000)


@export
def create_vault(vault_type: int, amount_of_tad: float,
                 amount_of_collateral: float):
    assert vault_type in vaults['list'], 'Not an available contract!'
    # interface enforcement is unnecessary because collateral types should be pre-vetted
    collateral = importlib.import_module(
        vaults[vault_type, 'collateral_type'])
    oracle = importlib.import_module(vaults['oracle'])

    price = oracle.get_price(vault_type)

    assert amount_of_tad > 0, 'Amount of tad must be positive!'
    assert vaults[vault_type, 'total'] + amount_of_tad <= vaults[vault_type,
                                                                 'cap'], 'The allowance is not sufficent!'

    assert fix_decimal((amount_of_collateral * price) / \
        amount_of_tad) >= vaults[vault_type,
                                'minimum_collateralization'], 'Not enough collateral!'

    cdp_number = cdp['current_value']
    cdp['current_value'] += 1

    cdp[cdp_number, 'owner'] = ctx.caller
    cdp[cdp_number, 'open'] = True

    cdp[cdp_number, 'collateral_type'] = vaults[vault_type, 'collateral_type']
    cdp[cdp_number, 'vault_type'] = vault_type
    cdp[cdp_number, 'tad'] = amount_of_tad
    cdp[cdp_number, 'collateral_amount'] = amount_of_collateral
    cdp[cdp_number, 'time'] = get_timestamp()

    collateral.approve(amount=amount_of_collateral, to=ctx.this)
    collateral.transfer_from(amount=amount_of_collateral,
                             to=ctx.this, main_account=ctx.caller)

    tad_contract.mint(amount=amount_of_tad)
    tad_contract.transfer(amount=amount_of_tad, to=ctx.caller)

    vaults[vault_type, 'issued'] += amount_of_tad
    vaults[vault_type, 'total'] += amount_of_tad

    return cdp_number


@export
def close_vault(cdp_number: int):
    assert cdp[cdp_number, 'owner'] == ctx.caller, 'Not the owner!'
    assert cdp[cdp_number, 'open'] == True, 'Vault has already been closed!'

    collateral = importlib.import_module(
        vaults[cdp[cdp_number, 'vault_type'], 'collateral_type'])

    stability_ratio = fix_decimal(vaults[cdp[cdp_number, 'vault_type'], 'total'] / \
        vaults[cdp[cdp_number, 'vault_type'], 'issued'])
    redemption_cost = cdp[cdp_number, 'tad'] * stability_ratio
    fee = redemption_cost * \
        (stability_rate[cdp[cdp_number, 'vault_type']] **
         (get_timestamp() - cdp[cdp_number, 'time'])) - redemption_cost

    amount = redemption_cost + fee
    tad_contract.transfer_from(
        amount=amount, to=ctx.this, main_account=ctx.caller)
    tad_contract.burn(amount=redemption_cost)

    stability_pool[cdp[cdp_number, 'vault_type']] += fee

    vaults[cdp[cdp_number, 'vault_type'], 'issued'] -= cdp[cdp_number, 'tad']
    # This is only different if the ratio is different
    vaults[cdp[cdp_number, 'vault_type'], 'total'] -= redemption_cost

    cdp[cdp_number, 'open'] = False

    # Return collateral
    collateral.transfer(
        amount=cdp[cdp_number, 'collateral_amount'], to=ctx.caller)

    return amount


@export
def fast_force_close_vault(cdp_number: int):
    assert_insufficent_collateral(cdp_number=cdp_number)
    assert cdp[cdp_number, 'open'] is True, 'Vault has already been closed!'

    collateral = importlib.import_module(
        vaults[cdp[cdp_number, 'vault_type'], 'collateral_type'])
    oracle = importlib.import_module(vaults['oracle'])

    stability_ratio = fix_decimal(vaults[cdp[cdp_number, 'vault_type'],
                             'total'] / vaults[cdp[cdp_number, 'vault_type'], 'issued'])
    redemption_cost_without_fee = cdp[cdp_number,
                                      'tad'] * stability_ratio
    redemption_cost = redemption_cost_without_fee * fix_decimal(1.1)
    fee = redemption_cost_without_fee * \
        (stability_rate[cdp[cdp_number, 'vault_type']]
         ** (get_timestamp() - cdp[cdp_number, 'time'])) - redemption_cost_without_fee
    redemption_cost += fee

    amount_of_collateral = cdp[cdp_number, 'collateral_amount']
    price = oracle.get_price(cdp[cdp_number, 'vault_type'])
    collateral_percent = fix_decimal((amount_of_collateral * price) / \
        redemption_cost)

    if collateral_percent >= fix_decimal(1.03):
        tad_contract.transfer_from(
            amount=redemption_cost, to=ctx.this, main_account=ctx.caller)
        tad_contract.burn(amount=redemption_cost_without_fee)
        amount = fix_decimal((redemption_cost * fix_decimal(1.03)) / price) # Double check this math is correct

        collateral.transfer(amount=amount, to=ctx.caller)
        collateral.transfer(amount=amount_of_collateral -
                            amount, to=cdp[cdp_number, 'owner'])

        vaults[cdp[cdp_number, 'vault_type'],
               'issued'] -= cdp[cdp_number, 'tad']
        vaults[cdp[cdp_number, 'vault_type'],
               'total'] -= redemption_cost_without_fee

    else:
        redemption_cost, redemption_cost_without_fee = redemption_cost * \
            fix_decimal(collateral_percent / fix_decimal(1.03)), redemption_cost_without_fee * \
            fix_decimal(collateral_percent / fix_decimal(1.03))

        tad_contract.transfer_from(
            amount=redemption_cost, to=ctx.this, main_account=ctx.caller)
        tad_contract.burn(amount=redemption_cost_without_fee)

        amount = cdp[cdp_number, 'collateral_amount']

        collateral.transfer(amount=amount, to=ctx.caller)

        vaults[cdp[cdp_number, 'vault_type'],
               'issued'] -= cdp[cdp_number, 'tad']
        vaults[cdp[cdp_number, 'vault_type'],
               'total'] -= redemption_cost_without_fee

    stability_pool[cdp[cdp_number, 'vault_type']
                   ] += redemption_cost - redemption_cost_without_fee

    cdp[cdp_number, 'open'] = False

    return amount


@export
def open_force_close_auction(cdp_number: int):
    assert_insufficent_collateral(cdp_number=cdp_number)

    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'
    assert cdp[cdp_number, 'auction',
               'open'] is not True, 'Auction is already taking place!' # Probably a redundant check, can be removed
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
        tad_contract.transfer_from(
            amount=amount - cdp[cdp_number, 'auction', ctx.caller, 'bid'],
            to=ctx.this, main_account=ctx.caller)

    else:
        tad_contract.transfer_from(
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
    tad_contract.burn(amount=cdp[cdp_number, 'auction', 'top_bid'] - fee)

    stability_pool[cdp[cdp_number, 'vault_type']] += fee

    vaults[cdp[cdp_number, 'vault_type'], 'issued'] -= cdp[cdp_number, 'tad']
    vaults[cdp[cdp_number, 'vault_type'],
           'total'] -= cdp[cdp_number, 'auction', 'top_bid'] - fee  # Fee is not burned, so it does not count

    return cdp[cdp_number, 'auction', 'highest_bidder'], cdp[cdp_number,
                                                             'auction', 'top_bid']


@export
def claim_unwon_bid(cdp_number: int):
    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'
    assert cdp[cdp_number, 'auction',
               'settled'] is True, 'Auction is still open or not opened!'

    tad_contract.transfer(
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
        return fix_decimal(vaults[vault_type, 'issued'] / vaults[vault_type, 'total'])

    else:  # This also applies to negatives and zeros, although those situations are unlikely
        vaults[vault_type, 'issued'] = vaults[vault_type, 'total']
        stability_pool[vault_type] -= default_amount

        return 1.0  # The ratio is perfectly equal


@export
def export_rewards(vault_type: int, amount: float):
    assert vaults[vault_type, 'DSR', 'owner'] == ctx.caller, 'Not the owner!'
    assert stability_pool[vault_type] >= amount, 'Not enough tad in stability pool to export!'

    stability_pool[vault_type] -= amount
    tad_contract.transfer(to=ctx.caller, amount=amount)

    return True


@export
def mint_rewards(amount: float):
    assert vaults['mint', 'DSR', 'owner'] == ctx.caller, 'Not the owner!'
    assert amount > 0, 'Cannot mint negative amount!'

    tad_contract.mint(amount=amount)
    tad_contract.transfer(to=ctx.caller, amount=amount)

    total_weight = 0
    total_funds = amount

    for vault_type in vaults['list']:
        total_weight += vaults[vault_type, 'weight']

    # To make the contract more robust, and to prevent floating point errors
    for vault_type in vaults['list']:
        funds_transferred = fix_decimal(
            vaults[vault_type, 'weight'] / total_weight) * total_funds
        vaults[vault_type, 'total'] += funds_transferred

        total_funds -= funds_transferred
        total_weight -= vaults[vault_type, 'weight']

    return True


@export
def sync_burn(vault_type: int, amount: float):
    assert vault_type in vaults['list'], 'Not an available contract!'

    tad_contract.transfer_from(
        to=ctx.this, amount=amount, main_account=ctx.caller)
    tad_contract.burn(amount=amount)

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
    vaults[vault_number, 'minimum_collateralization'] = collateral_amount
    vaults[vault_number, 'minimum_auction_time'] = auction_time
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
def change_any_state(key: Any, new_value: Any, convert_to_tuple: bool = False):
    assert vaults['OWNER'] == ctx.caller, 'Not the owner!'

    if convert_to_tuple:
        key = tuple(key)

    vaults[key] = new_value

    return new_value


@export
def change_stability_rate(key: int, new_value: float):
    assert vaults['OWNER'] == ctx.caller, 'Not the owner!'

    stability_rate[key] = new_value

    return new_value


@export
def get_collateralization_percent(cdp_number: int):
    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'
    oracle = importlib.import_module(vaults['oracle'])

    return cdp[cdp_number, 'collateral_amount'] * oracle.get_price(cdp[cdp_number, 'vault_type']) / cdp[cdp_number, 'tad']


def assert_insufficent_collateral(cdp_number: int):
    assert cdp[cdp_number, 'owner'] != 0, 'Nonexistent cdp'

    oracle = importlib.import_module(vaults['oracle'])

    assert (cdp[cdp_number, 'collateral_amount'] * oracle.get_price(cdp[cdp_number, 'vault_type']) / cdp[cdp_number, 'tad']) < \
        vaults[cdp[cdp_number, 'collateral_type'], 'minimum_collateralization'], 'Vault above minimum collateralization!'

    
def fix_decimal(old_decimal: float):
    temporary_var.set(old_decimal)
    new_decimal = temporary_var.get()
    
    return new_decimal
