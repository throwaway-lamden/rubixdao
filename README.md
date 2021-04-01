# lamden-mkr

![Python Version](https://img.shields.io/badge/Python-3.6-blue?style=flat-square)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/throwaway-lamden/lamden-mkr/tests?label=Tests&style=flat-square)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/throwaway-lamden/lamden-mkr/CodeQL?label=CodeQL&style=flat-square)

This repo contains the backend code for the Lamden MKR clone and some associated tests. 

## Testing

You can run unittests by calling the builtin python module.

```bash
python3 -m unittest test_refactor.py
```
For better performance, you can run tests multithreaded with [Pytest](https://pytest.org/), but this requires [pytest-xdist](https://github.com/pytest-dev/pytest-xdist) and [flaky](https://github.com/box/flaky).

```bash
pytest test_refactor.py -n {amount of threads} --force-flaky
```

You can see the current build status in the Actions tab of this repo.

## Deployment

Extract the smart contract code by appending the following to the smart contract you want to get, and then call it normally (`python3 {file}.py`)

```python
function = "name_of_function"
client = ContractingClient()
print(client.closure_to_code_string(function)[0]) #Prints only the code, and not the name of the function
```

You can now deploy this code via the wallet or by following the instructions in the [Contracting documentation](https://contracting.lamden.io/submitting/).

##  Dependencies

To test, `Contracting` and `Requests` are required. To deploy, `Lamden` or the browser wallet is required.

## Usage

Calling these contracts from other smart contracts is simple.
```python
import amm
amm.foo(bar, baz, etc.)
```
Calling these contracts from an application is harder. Refer to [Contracting documentation](https://contracting.lamden.io/), and [Lamden's GitHub page](https://github.com/Lamden/lamden).
```python
# TESTNET DEPLOYMENT EXAMPLE

from lamden.crypto import wallet, transaction
import requests

new_wallet = wallet.Wallet(seed=None) #Generates wallet. If you have an existing sk, put it here
print(new_wallet.verifying_key) #Prints vk
input() #Waits until next user input (to give time to send TAU)

kwargs = dict() #Add kwargs to dict

#Builds transaction
transaction.build_transaction(wallet=new_wallet,
contract="{contract}", 
function=f"{function}", 
kwargs=kwargs, 
nonce=nonce, #Starts at zero, increments with every transaction
processor="89f67bb871351a1629d66676e4bd92bbacb23bd0649b890542ef98f1b664a497", #Masternode address
stamps=stamp_limit) #Max amount of stamps you're willing to spend. As of 2021/02, the TAU/stamp ratio on mainnet is 1:36 

requests.post("https://testnet-master-1.lamden.io/", data = tx) #Submits transaction
```

## Modules

Placeholder

## Functions

### seed

**Cannot be called**

Sets the constants to their default value. As of now, you cannot pass arguments, and you have to manually modify the code.

The default values are as follows:
```python

```

### placeholder
Takes `contract: str, currency_amount: float=0, token_amount: float=0` 

## TODO

Make tense consistent in progress section

After documentation is completed, move `Progress` to progress.md

A test TODO section/file
