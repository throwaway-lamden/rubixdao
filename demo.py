from lamden.crypto import wallet, transaction
import requests, random

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
            stamps=300)
            
    requests.post('https://testnet-master-1.lamden.io/', data = tx)
    
    return nonce + 1
            
print("Lamden MKR Demo v1")
print("Colors may be broken on Windows machines")

new_wallet = wallet.Wallet(seed=None)
print(new_wallet.verifying_key)
input("Please press ENTER when you've sent dTAU to the demo address")

nonce = 0
contract_list = ['dai', 'oracle', 'vault', 'stake']
prefix = f'demo{random.randint(100000, 999999)}_' # To prevent issues with sending the SCs

for x in contract_list:
    print_color(f"Submitting {x} to blockchain as {prefix + x}", color.BOLD)
    
    with open(f'contracts/{x}') as f:
        kwargs = dict()
        kwargs['code'] = f.read().replace("importlib.import_module('vault_contract')", f"importlib.import_module('con_{prefix}_vault')").replace("importlib.import_module('dai_contract')", f"importlib.import_module('con_{prefix}_dai')") # Make a lot shorter
        kwargs['name'] = f'con_{prefix}_{x}'
        
        nonce = submit_transaction(new_wallet, 'submission', 'submit_contract', kwargs, nonce)

    time.sleep(2)
    
print_color("Finished submitting contracts", color.GREEN)
print_color("Setting oracle contract to correct contract", color.BOLD)

kwargs['key'] = f'oracle'
kwargs['new_state'] = f'con_{prefix}_oracle'

nonce = submit_transaction(new_wallet, f'con_{prefix}_vault', 'change_state', kwargs, nonce)

time.sleep(2)

print_color("Setting TAU price to 1 USD", color.BOLD)

kwargs['number'] = 0
kwargs['new_price'] = 1

tx, nonce = submit_transaction(new_wallet, f'con_{prefix}_oracle', 'set_price', kwargs, nonce)

time.sleep(2)

# Prep work finished, actual demo begins here
