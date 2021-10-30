# rubixdao

![Python Version](https://img.shields.io/badge/Python-3.6-blue?style=flat-square)
![Dependencies](https://img.shields.io/badge/Dependencies-contracting%2C%20requests-blue?style=flat-square)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/throwaway-lamden/rubixdao/tests?label=Tests&style=flat-square)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/throwaway-lamden/rubixdao/CodeQL?label=CodeQL&style=flat-square)

This repository contains the backend code for the RubixDAO clone and some associated tests.

## Testing

You can run the included unittests with the [Pytest](https://pytest.org/) framework.

```bash
python3 -m pytest contracts/tests/\*
```
For better performance, you can run tests multithreaded with [pytest-xdist](https://github.com/pytest-dev/pytest-xdist) and [flaky](https://github.com/box/flaky).

```bash
python3 -m pytest tests -n {amount of threads} --force-flaky
```

You can see the current build status in the [Actions](https://github.com/throwaway-lamden/rubixdao/actions) tab of this repository.

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

## Demo

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/throwaway-lamden/rubixdao/demo?label=Demo&style=flat-square)

*The demo is untested and a WIP. It may not always be up-to-date. The GitHub action is flaky because it uses the actual blockchain, so it may take several runs to succeed if the blockchain is under high load.*

To see the contracts in action on the testnet, clone this repository and run `demo.py`. The dependencies are `Lamden` and `requests`. If you are running the script on Windows, `colorama` is recommended.

You can also see the demo in the [Github Actions demo.yml](https://github.com/throwaway-lamden/rubixdao/actions/workflows/demo.yml) tab. A WIP web demo on [Repl.it](https://replit.com/@testtestlamden/rubixdao) can also be used.

### Expected Workflows

1. User opens vault -> waits ? amount of time -> stakes tad/sells tad -> withdraws stake/buys back tad -> closes vault with initial tad and stability fee and gets collateral back
2. User opens vault -> waits ? amount of time -> collateral value drops -> anyone can force close the vault instantly and get 3% profit
3. User opens vault -> waits ? amount of time -> collateral value drops -> anyone can open an auction -> after 72 hours has passed, the highest tad bid can claim the collateral and everyone else can claim their bids back
## Usage

Calling these contracts from other smart contracts is simple.
```python
import mkr
mkr.foo(bar, baz, etc.)
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
function='{function}',
kwargs=kwargs,
nonce={nonce}, # Starts at zero, increments with every transaction
processor='89f67bb871351a1629d66676e4bd92bbacb23bd0649b890542ef98f1b664a497', # Masternode address
stamps={stamp_limit}) # Max amount of stamps you're willing to spend. As of 2021/02, the TAU/stamp ratio on mainnet is 1:65

requests.post('https://testnet-master-1.lamden.io/', data = tx) # Submits transaction
```

## Modules

### vault

This is the main SC. It handles creating CDPs and closing CDPs as well as auctions for undercollateralized CDPs. This contract should be the only contract that can mint tad. The staking contract (`stake.py`) calls this to pay out rewards. As well, future contracts can pay stability pool rewards to lMKR holders with `export_rewards()`.

[Contract](https://github.com/throwaway-lamden/rubixdao/blob/main/contracts/vault.py)

[Documentation](https://github.com/throwaway-lamden/rubixdao/blob/main/documentation/vault.md)

### stake

This is the equivalent to the DSR. It has an adjustable interest rate. Payouts are made through the vault contract. The staked token conforms to LST-001 and LST-002.

[Contract](https://github.com/throwaway-lamden/rubixdao/blob/main/contracts/stake.py)

[Documentation](https://github.com/throwaway-lamden/rubixdao/blob/main/documentation/stake.md)

### tad

This is the tad equivalent. It conforms to LST-001 and LST-002.

[Contract](https://github.com/throwaway-lamden/rubixdao/blob/main/contracts/tad.py)

[Documentation](https://github.com/throwaway-lamden/rubixdao/blob/main/documentation/tad.md)

### oracle

This is the base oracle contract.

[Contract](https://github.com/throwaway-lamden/rubixdao/blob/main/contracts/oracle.py)

[Documentation](https://github.com/throwaway-lamden/rubixdao/blob/main/documentation/oracle.md)

## API Guide

*The primary documentation should always be the [Official Lamden Documentation](https://docs.lamden.io). This section only serves as a TL;DR.*

|         | Masternode                         | Block Explorer            |
|---------|------------------------------------|---------------------------|
| Testnet | https://testnet-master-1.lamden.io | https://testnet.lamden.io |
| Mainnet | https://masternode-01.lamden.io    | https://mainnet.lamden.io |

`{masternode}` refers to the masternode address you are using:

`GET` state with `{masternode}/contract/{hash}?key={key}`.

`GET` latest block number with `{masternode}/contract/{hash}?key={key}`.

`GET` a block with `{masternode}/blocks?num={block_number}`

`GET` the results of a tx with `{masternode}/tx?hash={hash}`

`POST` a tx to `{masternode}/`.

## TODO

Make tense consistent in progress section

A test TODO section/file

Demo script w/ optional colorama for non-ANSI compatible OSes

Record gif of demo script (possibly with asciinemia) and add to readme
