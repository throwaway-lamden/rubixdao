from lamden.crypto import wallet, transaction
import requests, random, time, ast

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
    
def submit_transaction(wallet, contract, function, kwargs, nonce):
    tx = transaction.build_transaction(wallet=wallet,
            contract=contract,
            function=function,
            kwargs=kwargs,
            nonce=nonce, # Starts at zero, increments with every transaction
            processor='89f67bb871351a1629d66676e4bd92bbacb23bd0649b890542ef98f1b664a497', # Masternode address
            stamps=1000)
            
    return_data = requests.post('https://testnet-master-1.lamden.io/', data = tx).content
    return_data = return_data.decode("UTF-8")
    return_data = ast.literal_eval(return_data)
    
    try:
        print(return_data['hash'])
    except KeyError:
        print_color(f"Transaction failed, debug data: {str(return_data['error'])}", color.RED)
    
    return nonce + 1, return_data
            
print("Lamden MKR Demo v1")
print("Colors may be broken on Windows machines")

new_wallet = wallet.Wallet(seed=None)

try:
    requests.get(f"https://faucet.lamden.io/.netlify/functions/send?account={new_wallet.verifying_key}")
    print_color("500 dTAU funded from faucet", color.GREEN)
    
except Exception as e:
    print_color(f'Automatic funding failed with {repr(e)}', color.RED)
    print(new_wallet.verifying_key)
    input("Please press ENTER when you've sent dTAU to the demo address")

nonce = 0
contract_list = ['dai', 'oracle', 'vault', 'stake']
prefix = f'demo{random.randint(100000, 999999)}' # To prevent issues with sending the SCs

for x in contract_list:
    print_color(f"Submitting {x} contract to testnet as con_{prefix + '_' + x}", color.BOLD)
    
    with open(f'contracts/{x}.py') as f:
        kwargs = dict()
        kwargs['code'] = f.read().replace("importlib.import_module('vault_contract')", f"importlib.import_module('con_{prefix}_vault')").replace("importlib.import_module('dai_contract')", f"importlib.import_module('con_{prefix}_dai')") # Make a lot shorter
        kwargs['name'] = f'con_{prefix}_{x}'
        
        if x == "dai":
            kwargs['constructor_args'] = dict(owner = f'con_{prefix}_vault')
            
        nonce, result = submit_transaction(new_wallet, 'submission', 'submit_contract', kwargs, nonce)

    time.sleep(2)
    
print_color("Finished submitting contracts", color.GREEN)

print_color("Setting oracle contract to correct contract", color.BOLD)

kwargs = dict() # Reset dict
kwargs['key'] = f'oracle'
kwargs['new_value'] = f'con_{prefix}_oracle'

nonce, result = submit_transaction(new_wallet, f'con_{prefix}_vault', 'change_state', kwargs, nonce)

time.sleep(2)

print_color("Setting stability rate to 3.2% per year", color.BOLD)

kwargs = dict() # Reset dict
kwargs['key'] = f'stability_rate'
kwargs['new_value'] = 1.0000000015469297

nonce, result = submit_transaction(new_wallet, f'con_{prefix}_vault', 'change_any_state', kwargs, nonce)

time.sleep(2)

print_color("Setting TAU price to 1 USD", color.BOLD)

kwargs = dict()
kwargs['number'] = 0
kwargs['new_price'] = 1

nonce, result = submit_transaction(new_wallet, f'con_{prefix}_oracle', 'set_price', kwargs, nonce)

time.sleep(2)

print_color("Approving dTAU for spending", color.BOLD)

for x in contract_list:
    kwargs = dict()
    kwargs['amount'] = 1000
    kwargs['to'] = f'con_{prefix}_{x}'

    nonce, result = submit_transaction(new_wallet, f'currency', 'approve', kwargs, nonce)
    nonce, result = submit_transaction(new_wallet, f'con_{prefix}_dai', 'approve', kwargs, nonce)
    
    time.sleep(2)

# Prep work finished, actual demo begins here
print_color("Setup complete, main demo beginning", color.GREEN)

print_color("Creating vault buffer to offset stability fee", color.BOLD)

kwargs = dict()
kwargs['vault_type'] = 0
kwargs['amount_of_dai'] = 1
kwargs['amount_of_collateral'] = 2

nonce, result = submit_transaction(new_wallet, f'con_{prefix}_vault', 'create_vault', kwargs, nonce)

print_color("Creating 100 DAI vault with 200 dTAU as collateral", color.BOLD)

kwargs = dict()
kwargs['vault_type'] = 0
kwargs['amount_of_dai'] = 100
kwargs['amount_of_collateral'] = 200

nonce, result = submit_transaction(new_wallet, f'con_{prefix}_vault', 'create_vault', kwargs, nonce)

input("Please press ENTER when you want to close the vault")

print_color("Closing vault", color.BOLD)

kwargs = dict()
kwargs['cdp_number'] = 1

nonce, result = submit_transaction(new_wallet, f'con_{prefix}_vault', 'close_vault', kwargs, nonce)

time.sleep(2)

close_price = requests.get(f"https://testnet-master-1.lamden.io/tx?hash={result['hash']}").json()['result']
print_color(f"Vault closed for {close_price} DAI (additional DAI is from stability fee)", color.CYAN)
