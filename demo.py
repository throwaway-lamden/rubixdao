import ast
import os
import random
import sys
import time

import requests
from lamden.crypto import transaction, wallet


class SubmissionError(Exception):
    pass


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_color(text, color_type):
    print(color_type + text + color.END)


def print_color_alternate(text, color_type):
    print(color_type + text)


def print_color_none(text, color_type):
    print(text)


def submit_transaction(wallet, contract, function, kwargs, nonce):
    fail = False
    while True:  # TODO: Remove later, the check that used this is now depreceated
        tx = transaction.build_transaction(wallet=wallet,
                                           contract=contract,
                                           function=function,
                                           kwargs=kwargs,
                                           nonce=nonce,  # Starts at zero, increments with every transaction
                                           # Masternode address
                                           processor='89f67bb871351a1629d66676e4bd92bbacb23bd0649b890542ef98f1b664a497',
                                           stamps=1000)

        try:
            return_data = requests.post(
                'https://testnet-master-1.lamden.io/', data=tx).content
            return_data = return_data.decode("UTF-8")
            return_data = ast.literal_eval(return_data)
            print(return_data['hash'])
        except KeyError:
            # Raises error on second try (so it doesn't continuously retry)
            try:
                print_color(
                    f"Transaction failed, debug data: {str(return_data['error'])}", color.RED)
                print_color(
                    f"Retrying...", color.RED)

                return_data = requests.post(
                    'https://testnet-master-1.lamden.io/', data=tx).content
                return_data = return_data.decode("UTF-8")
                return_data = ast.literal_eval(return_data)
                print(return_data['hash'])
            except KeyError:
                raise SubmissionError(str(return_data['error']))

            continue

        return nonce + 1, return_data


print("Lamden MKR Demo v1")
print("Colors may be broken on Windows machines")

plat = sys.platform
supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                              'ANSICON' in os.environ)

if supported_platform != True:
    print("Color is not natively supported on this platform, trying colorama")

    try:
        from colorama import Fore, Style, init

        class color_alternate:
            PURPLE = '\033[95m'
            CYAN = Fore.CYAN
            DARKCYAN = '\033[36m'
            BLUE = '\033[94m'
            GREEN = Fore.GREEN
            YELLOW = Fore.YELLOW
            RED = Fore.RED
            BOLD = Style.BRIGHT
            UNDERLINE = '\033[4m'

        color = color_alternate
        print_color = print_color_alternate

        init(autoreset=True)

    except ImportError:
        print("Unable to import colorama, defaulting to no colors")
        print_color = print_color_none


new_wallet = wallet.Wallet(seed=None)

try:
    requests.get(
        f"https://faucet.lamden.io/.netlify/functions/send?account={new_wallet.verifying_key}")
    print_color("500 dTAU funded from faucet", color.GREEN)

except Exception as e:
    print_color(f'Automatic funding failed with {repr(e)}', color.RED)
    print(new_wallet.verifying_key)
    input("Please press ENTER when you've sent dTAU to the demo address")

nonce = 0
contract_list = ['dai', 'oracle', 'vault', 'stake']
# To prevent issues with sending the SCs
prefix = f'demo{random.randint(100000, 999999)}'

for x in contract_list:
    print_color(
        f"Submitting {x} contract to testnet as con_{prefix + '_' + x}", color.BOLD)

    with open(f'contracts/{x}.py') as f:
        kwargs = dict()
        kwargs['code'] = f.read().replace("importlib.import_module('vault_contract')", f"importlib.import_module('con_{prefix}_vault')").replace(
            "importlib.import_module('dai_contract')", f"importlib.import_module('con_{prefix}_dai')")  # Make a lot shorter
        kwargs['name'] = f'con_{prefix}_{x}'

        if x == "dai":
            kwargs['constructor_args'] = dict(owner=f'con_{prefix}_vault')

        nonce, result = submit_transaction(
            new_wallet, 'submission', 'submit_contract', kwargs, nonce)

    time.sleep(2)

print_color("Finished submitting contracts", color.GREEN)

print_color("Setting oracle contract to correct contract", color.BOLD)

kwargs = dict()  # Reset dict
kwargs['key'] = f'oracle'
kwargs['new_value'] = f'con_{prefix}_oracle'

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'change_state', kwargs, nonce)

time.sleep(2)

print_color("Setting stability rate to 5% per year", color.BOLD)

kwargs = dict()  # Reset dict
kwargs['key'] = 0
kwargs['new_value'] = dict(__fixed__='1.0000000015469297')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'change_stability_rate', kwargs, nonce)

time.sleep(2)

print_color("Setting TAU price to 1 USD", color.BOLD)

kwargs = dict()
kwargs['number'] = 0
kwargs['new_price'] = dict(__fixed__='1.0')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_oracle', 'set_price', kwargs, nonce)

time.sleep(2)

print_color("Approving dTAU for spending", color.BOLD)

for x in contract_list:
    kwargs = dict()
    kwargs['amount'] = dict(__fixed__='1000.0')
    kwargs['to'] = f'con_{prefix}_{x}'

    nonce, result = submit_transaction(
        new_wallet, f'currency', 'approve', kwargs, nonce)
    nonce, result = submit_transaction(
        new_wallet, f'con_{prefix}_dai', 'approve', kwargs, nonce)

    time.sleep(2)

# Prep work finished, actual demo begins here
print_color("Setup complete, main demo beginning", color.GREEN)
print_color("Demo 1: Basic vault open/close", color.GREEN)
print_color("Creating vault buffer to offset stability fee", color.BOLD)

kwargs = dict()
kwargs['vault_type'] = 0
kwargs['amount_of_dai'] = dict(__fixed__='25.0')
kwargs['amount_of_collateral'] = dict(__fixed__='38.0')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'create_vault', kwargs, nonce)

print_color("Creating 100 DAI vault with 155 dTAU as collateral", color.BOLD)

kwargs = dict()
kwargs['vault_type'] = 0
kwargs['amount_of_dai'] = dict(__fixed__='100.0')
kwargs['amount_of_collateral'] = dict(__fixed__='155.0')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'create_vault', kwargs, nonce)

try:
    input("Please press ENTER when you want to close the vault")
except EOFError:
    print_color(
        "\nError with input. If this is run in GitHub Actions, ignore.", color.RED)

print_color("Closing vault", color.BOLD)
kwargs = dict()
kwargs['cdp_number'] = 1

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'close_vault', kwargs, nonce)

time.sleep(2)

# close_price = requests.get(f"https://testnet-master-1.lamden.io/tx?hash={result['hash']}").json()['result'] fails because it returns a decimal object instead of a human readable number
close_price = abs(float(ast.literal_eval(requests.get(
    f"https://testnet-master-1.lamden.io/contracts/con_{prefix}_dai/balances?key={new_wallet.verifying_key}").content.decode("UTF-8"))['value']['__fixed__']) - 25)
print_color(
    f"Vault closed for 100 DAI and an additional {close_price} DAI stability fee", color.CYAN)

# TODO: Make function to decode bytes dict

try:
    input("Please press ENTER when you want to proceed")
except EOFError:
    print_color(
        "\nError with input. If this is run in GitHub Actions, ignore.", color.RED)

print_color("Demo 2: Staking demo", color.GREEN)

print_color("Setting staking contract to correct contract", color.BOLD)

kwargs = dict()  # Reset dict
kwargs['key'] = ('mint', 'DSR', 'owner')
kwargs['convert_to_tuple'] = True
kwargs['new_value'] = f'con_{prefix}_stake'

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'change_any_state', kwargs, nonce)

time.sleep(2)

print_color("Creating 100 DAI vault with 155 dTAU as collateral", color.BOLD)

kwargs = dict()
kwargs['vault_type'] = 0
kwargs['amount_of_dai'] = dict(__fixed__='100.0')
kwargs['amount_of_collateral'] = dict(__fixed__='155.0')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'create_vault', kwargs, nonce)

time.sleep(2)

print_color("Staking 100 DAI at a rate of 5% per annum", color.BOLD)

kwargs = dict()
kwargs['amount'] = dict(__fixed__='100.0')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_stake', 'stake', kwargs, nonce)

time.sleep(2)

try:
    input("Please press ENTER when you want to unstake")
except EOFError:
    print_color(
        "\nError with input. If this is run in GitHub Actions, ignore.", color.RED)

print_color("Unstaking 100 DAI", color.BOLD)

s_amount = float(ast.literal_eval(requests.get(
    f"https://testnet-master-1.lamden.io/contracts/con_{prefix}_stake/balances?key={new_wallet.verifying_key}").content.decode("UTF-8"))['value']['__fixed__']) - 0.00000000000001  # Prevent floating point issue

old_amount = float(ast.literal_eval(requests.get(
    f"https://testnet-master-1.lamden.io/contracts/con_{prefix}_dai/balances?key={new_wallet.verifying_key}").content.decode("UTF-8"))['value']['__fixed__'])

kwargs = dict()
kwargs['amount'] = dict(__fixed__=str(s_amount))

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_stake', 'withdraw_stake', kwargs, nonce)

time.sleep(2)

return_amount = float(ast.literal_eval(requests.get(
    f"https://testnet-master-1.lamden.io/contracts/con_{prefix}_dai/balances?key={new_wallet.verifying_key}").content.decode("UTF-8"))['value']['__fixed__']) - old_amount

print_color(
    f"Stake closed for 100 DAI and an additional {return_amount - 100.0} DAI interest", color.CYAN)  # TODO: Make operation consistent

print_color("Closing vault", color.BOLD)
kwargs = dict()
kwargs['cdp_number'] = 2

old_amount = float(ast.literal_eval(requests.get(
    f"https://testnet-master-1.lamden.io/contracts/con_{prefix}_dai/balances?key={new_wallet.verifying_key}").content.decode("UTF-8"))['value']['__fixed__'])

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'close_vault', kwargs, nonce)

time.sleep(2)

close_price = abs(old_amount - float(ast.literal_eval(requests.get(
    f"https://testnet-master-1.lamden.io/contracts/con_{prefix}_dai/balances?key={new_wallet.verifying_key}").content.decode("UTF-8"))['value']['__fixed__']))
print_color(
    f"Vault closed for 100 DAI and an additional {close_price - 100.0} DAI stability fee. The overall profit from staking is {return_amount - close_price} (this will likely be negative).", color.CYAN)

print_color("Demo 3: Undercollateralized instant force close demo", color.GREEN)
print_color("Not implemented yet", color.BOLD)

try:
    input("Please press ENTER when you want to proceed")
except EOFError:
    print_color(
        "\nError with input. If this is run in GitHub Actions, ignore.", color.RED)

print_color("Demo 4: Undercollateralized auction force close demo", color.GREEN)
print_color("Not implemented yet", color.BOLD)

try:
    input("Please press ENTER when you want to proceed")
except EOFError:
    print_color(
        "\nError with input. If this is run in GitHub Actions, ignore.", color.RED)

if os.environ.get("GITHUB_ACTIONS") != "true":
    print_color(
        f'The private key used in this demo was {new_wallet.signing_key}', color.GREEN + color.BOLD)
else:
    print_color(f'The private key used in this demo is omitted because this was run in GitHub Actions',
                color.YELLOW + color.BOLD)

# todo: send back all the extra funds
# todo: change fee for staking to 25% (1.0000000070758357) so rewards will be positive instead of negative
