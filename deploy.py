from solcx import compile_source, install_solc
from web3 import Web3

install_solc('0.8.0')

with open('contract.sol', 'r') as f:
    contract_source = f.read()

compiled = compile_source(contract_source, solc_version='0.8.0')
contract_interface = compiled['<stdin>:EvidenceStorage']

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
w3.eth.default_account = w3.eth.accounts[0]

# Deploy
EvidenceStorage = w3.eth.contract(
    abi=contract_interface['abi'],
    bytecode=contract_interface['bin']
)

tx_hash = EvidenceStorage.constructor().transact()
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("✅ Contract deployed!")
print("📍 Contract Address:", receipt.contractAddress)