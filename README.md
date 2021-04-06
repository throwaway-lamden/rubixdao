# lamden-mkr

![Python Version](https://img.shields.io/badge/Python-3.6-blue?style=flat-square)
![Dependencies](https://img.shields.io/badge/Dependencies-contracting%2C%20requests-blue?style=flat-square)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/throwaway-lamden/lamden-mkr/tests?label=Tests&style=flat-square)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/throwaway-lamden/lamden-mkr/CodeQL?label=CodeQL&style=flat-square)

This repository contains the backend code for the Lamden MKR clone and some associated tests.

## Progress

You can see the current progress of the project in [progress.md](https://github.com/throwaway-lamden/lamden-mkr/blob/main/documentation/progress.md).

## Testing

You can run the included unittests with the [Pytest](https://pytest.org/) framework.

```bash
python3 -m pytest contracts/tests/\*
```
For better performance, you can run tests multithreaded with [pytest-xdist](https://github.com/pytest-dev/pytest-xdist) and [flaky](https://github.com/box/flaky).

```bash
python3 -m pytest tests -n {amount of threads} --force-flaky
```

You can see the current build status in the [Actions](https://github.com/throwaway-lamden/lamden-mkr/actions) tab of this repository.

## Deployment

Extract the smart contract code by appending the following to the smart contract you want to get, and then call it normally (`python3 {file}.py`)

```python
function = 'name_of_function'
client = ContractingClient()
print(client.closure_to_code_string(function)[0]) # Prints only the code, and not the name of the function
```

You can now deploy this code via the wallet or by following the instructions in the [Contracting documentation](https://contracting.lamden.io/submitting/).

## Dependencies

To test, `contracting`, `requests`, and `pytest` are required. To deploy, `Lamden` or the browser wallet is required.

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

new_wallet = wallet.Wallet(seed=None) # Generates wallet. If you have an existing sk, put it here
print(new_wallet.verifying_key) # Prints vk
input() # Waits until next user input (to give time to send TAU)

kwargs = dict() # Add kwargs to dict

# Builds transaction
tx = transaction.build_transaction(wallet=new_wallet,
contract='{contract}',
function=f'{function}',
kwargs=kwargs,
nonce=nonce, # Starts at zero, increments with every transaction
processor='89f67bb871351a1629d66676e4bd92bbacb23bd0649b890542ef98f1b664a497', # Masternode address
stamps=stamp_limit) # Max amount of stamps you're willing to spend. As of 2021/02, the TAU/stamp ratio on mainnet is 1:65

requests.post('https://testnet-master-1.lamden.io/', data = tx) # Submits transaction
```

## Modules

### vault

This is the main SC. It handles creating CDPs and closing CDPs as well as auctions for undercollateralized CDPs. This contract should be the only contract that can mint DAI. The staking contract (`stake.py`) calls this to pay out rewards. As well, future contracts can pay stability pool rewards to lMKR holders with `export_rewards()`.

[Contract](https://github.com/throwaway-lamden/lamden-mkr/blob/main/contracts/vault.py)

[Documentation]()

### stake

This is the equivalent to the DSR. It has an adjustable interest rate. Payouts are made through the vault contract. The staked token conforms to LST-001 and LST-002.

[Contract](https://github.com/throwaway-lamden/lamden-mkr/blob/main/contracts/stake.py)

[Documentation]()

### dai

This is the DAI equivalent. It conforms to LST-001 and LST-002.

[Contract](https://github.com/throwaway-lamden/lamden-mkr/blob/main/contracts/dai.py)

[Documentation]()

### oracle

This is the base oracle contract.

[Contract](https://github.com/throwaway-lamden/lamden-mkr/blob/main/contracts/oracle.py)

[Documentation]()

## API Guide

*The primary documentation should always be the [Official Lamden Documentation](https://docs.lamden.io). This section only serves as a TL;DR.*

Placeholder

## TODO

Make tense consistent in progress section

A test TODO section/file

Demo script

Record video of demo script and add to readme
