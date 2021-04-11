# This demo is obselete
import ast
import time
import random
import requests
from colorama import init, Fore, Style
from lamden.crypto import wallet, transaction
assert False, 'This demo is obsolete!'


init(autoreset=True)


def submit_transaction(wallet, contract, function, kwargs, nonce):
    tx = transaction.build_transaction(wallet=wallet,
                                       contract=contract,
                                       function=function,
                                       kwargs=kwargs,
                                       nonce=nonce,  # Starts at zero, increments with every transaction
                                       # Masternode address
                                       processor='89f67bb871351a1629d66676e4bd92bbacb23bd0649b890542ef98f1b664a497',
                                       stamps=1000)

    return_data = requests.post(
        'https://testnet-master-1.lamden.io/', data=tx).content
    return_data = return_data.decode("UTF-8")
    return_data = ast.literal_eval(return_data)

    try:
        print(return_data['hash'])
    except KeyError:
        print(
            Fore.RED + f"Transaction failed, debug data: {str(return_data['error'])}")

    return nonce + 1, return_data


print("Lamden MKR Demo v1")
print("Colors may be broken on Windows machines")

new_wallet = wallet.Wallet(seed=None)

try:
    requests.get(
        f"https://faucet.lamden.io/.netlify/functions/send?account={new_wallet.verifying_key}")
    print(Fore.GREEN + "500 dTAU funded from faucet")

except Exception as e:
    print(Fore.RED + f'Automatic funding failed with {repr(e)}')
    print(new_wallet.verifying_key)
    input("Please press ENTER when you've sent dTAU to the demo address")

nonce = 0
contract_list = ['dai', 'oracle', 'vault', 'stake']
# To prevent issues with sending the SCs
prefix = f'demo{random.randint(100000, 999999)}'

for x in contract_list:
    print(
        Style.BRIGHT + f"Submitting {x} contract to testnet as con_{prefix + '_' + x}")

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

print(Fore.GREEN + "Finished submitting contracts")

print(Style.BRIGHT + "Setting oracle contract to correct contract")

kwargs = dict()  # Reset dict
kwargs['key'] = f'oracle'
kwargs['new_value'] = f'con_{prefix}_oracle'

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'change_state', kwargs, nonce)

time.sleep(2)

print(Style.BRIGHT + "Setting stability rate to 3.2% per year")

kwargs = dict()  # Reset dict
kwargs['key'] = 0
kwargs['new_value'] = dict(__fixed__='1.0000000015469297')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'change_stability_rate', kwargs, nonce)

time.sleep(2)

print(Style.BRIGHT + "Setting TAU price to 1 USD")

kwargs = dict()
kwargs['number'] = 0
kwargs['new_price'] = dict(__fixed__='1.0')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_oracle', 'set_price', kwargs, nonce)

time.sleep(2)

print(Style.BRIGHT + "Approving dTAU for spending")

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
print(Fore.GREEN + "Setup complete, main demo beginning")
print(Style.BRIGHT + "Creating vault buffer to offset stability fee")

kwargs = dict()
kwargs['vault_type'] = 0
kwargs['amount_of_dai'] = dict(__fixed__='1.0')
kwargs['amount_of_collateral'] = dict(__fixed__='2.0')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'create_vault', kwargs, nonce)

print(Style.BRIGHT + "Creating 100 DAI vault with 200 dTAU as collateral")

kwargs = dict()
kwargs['vault_type'] = 0
kwargs['amount_of_dai'] = dict(__fixed__='100.0')
kwargs['amount_of_collateral'] = dict(__fixed__='200.0')

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'create_vault', kwargs, nonce)

input("Please press ENTER when you want to close the vault")

print(Style.BRIGHT + "Closing vault")
kwargs = dict()
kwargs['cdp_number'] = 1

nonce, result = submit_transaction(
    new_wallet, f'con_{prefix}_vault', 'close_vault', kwargs, nonce)

time.sleep(2)

# close_price = requests.get(f"https://testnet-master-1.lamden.io/tx?hash={result['hash']}").json()['result'] fails because it returns a decimal object instead of a human readable number
close_price = abs(float(ast.literal_eval(requests.get(
    f"https://testnet-master-1.lamden.io/contracts/con_{prefix}_dai/balances?key={new_wallet.verifying_key}").content.decode("UTF-8"))['value']['__fixed__']) - 1)
print(Fore.CYAN +
      f"Vault closed for 100 DAI and an additional {close_price} DAI stability fee")
# TODO: Make function to decode bytes dict
