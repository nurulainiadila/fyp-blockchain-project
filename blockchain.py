from web3 import Web3

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

# Your exact contract address from the deployment step
CONTRACT_ADDRESS = '0x5cCfbEa1bc0c99c92CAa2EDd62289B33bDaF315B'

# The ABI acts as the "menu" telling Python what functions the contract has
CONTRACT_ABI = [
    {
        "inputs": [{"name": "_hash", "type": "string"}, {"name": "_caseID", "type": "string"}],
        "name": "storeEvidence",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [{"name": "index", "type": "uint256"}],
        "name": "getEvidence",
        "outputs": [
            {"name": "", "type": "string"},
            {"name": "", "type": "string"},
            {"name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
w3.eth.default_account = w3.eth.accounts[0]

def store_on_blockchain(evidence_hash, case_id):
    """Saves the SHA-256 hash to the Ganache blockchain"""
    tx = contract.functions.storeEvidence(evidence_hash, case_id).transact()
    w3.eth.wait_for_transaction_receipt(tx)
    return True

def get_all_evidence():
    """Retrieves all stored evidence records"""
    count = contract.functions.getCount().call()
    all_evidence = []
    for i in range(count):
        hash_val, case_id, timestamp = contract.functions.getEvidence(i).call()
        all_evidence.append({
            "index": i,
            "hash": hash_val,
            "case_id": case_id,
            "timestamp": timestamp
        })
    return all_evidence

def verify_hash(input_hash):
    """Queries the blockchain to verify if a hash exists"""
    count = contract.functions.getCount().call()
    for i in range(count):
        stored_hash, case_id, timestamp = contract.functions.getEvidence(i).call()
        if stored_hash == input_hash:
            return True, case_id
    return False, None