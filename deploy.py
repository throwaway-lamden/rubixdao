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
                                           processor='5b09493df6c18d17cc883ebce54fcb1f5afbd507533417fe32c006009a9c3c4a',
                                           stamps=1500)

        try:
            return_data = requests.post(
                'https://masternode-01.lamden.io/', data=tx).content
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
                    'https://masternode-01.lamden.io/', data=tx).content
                return_data = return_data.decode("UTF-8")
                return_data = ast.literal_eval(return_data)
                print(return_data['hash'])
            except KeyError:
                raise SubmissionError(str(return_data['error']))

            continue

        return nonce + 1, return_data


print("RubixDAO Deployment v1")

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

try: 
    new_wallet = wallet.Wallet(seed=sys.argv[1])
    cli_seed = True
    
except ValueError: # otherwise, will error if only prefix given
    new_wallet = wallet.Wallet(seed=None)
    cli_seed = False

print(new_wallet.verifying_key, new_wallet.signing_key)
input("Please press ENTER when you've sent TAU to the demo address")

nonce = requests.get(f'https://masternode-01.lamden.io/nonce/{new_wallet.verifying_key}').json()['nonce']
contract_list = ['tad', 'oracle', 'vault', 'stake']

if cli_seed:
    prefix = str(sys.argv[2]) 
else: # no try except because we want this to fail if no prefix is given
    prefix = str(sys.argv[1])
    
for x in contract_list:
    print_color(
        f"Submitting {x} contract to mainnet as con_{prefix + '_' + x}", color.BOLD)

    with open(f'contracts/{x}.py') as f:
        kwargs = dict()
        kwargs['code'] = f.read().replace("importlib.import_module('vault_contract')", f"importlib.import_module('con_{prefix}_vault')").replace(
            "importlib.import_module('tad_contract')", f"importlib.import_module('con_{prefix}_tad')")  # Make a lot shorter
        kwargs['name'] = f'con_{prefix}_{x}'

        if x == "tad":
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

print_color("Setup complete", color.GREEN)

