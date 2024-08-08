from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware #Necessary for POA chains
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"

def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def getContractInfo(chain):
    """
        Load the contract_info file into a dictinary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( "Failed to read contract info" )
        print( "Please contact your instructor" )
        print( e )
        sys.exit(1)

    return contracts[chain]

def register_and_create_tokens():
    # Read the token addresses from the CSV
    tokens_df = pd.read_csv(erc20s_csv)
    
    # Connect to the source and destination chains
    source_w3 = connectTo('avax')
    destination_w3 = connectTo('bsc')
    
    # Get the contract information
    source_contract_data = getContractInfo('source')
    destination_contract_data = getContractInfo('destination')
    
    source_contract = source_w3.eth.contract(
        address=source_contract_data['address'],
        abi=source_contract_data['abi']
    )
    destination_contract = destination_w3.eth.contract(
        address=destination_contract_data['address'],
        abi=destination_contract_data['abi']
    )
    
    # Register and create tokens
    for index, row in tokens_df.iterrows():
        token_address = row['address']
        
        # Register the token on the source chain
        nonce = source_w3.eth.get_transaction_count(source_contract_data['address'])
        tx = source_contract.functions.registerToken(token_address).buildTransaction({
            'chainId': 43113,
            'gas': 2000000,
            'gasPrice': source_w3.toWei('50', 'gwei'),
            'nonce': nonce,
        })
        sign_and_send_transaction(source_w3, tx)
        
        # Create the corresponding token on the destination chain
        nonce = destination_w3.eth.get_transaction_count(destination_contract_data['address'])
        tx = destination_contract.functions.createToken(
            token_address, 
            "WrappedToken" + str(index + 1),  # Arbitrary name
            "WT" + str(index + 1)  # Arbitrary symbol
        ).buildTransaction({
            'chainId': 97,
            'gas': 2000000,
            'gasPrice': destination_w3.toWei('50', 'gwei'),
            'nonce': nonce,
        })
        sign_and_send_transaction(destination_w3, tx)

def scanBlocks(chain):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return

    w3 = connectTo(source_chain if chain == 'source' else destination_chain)
    contract_data = getContractInfo('source' if chain == 'source' else 'destination')
    contract = w3.eth.contract(address=contract_data['address'], abi=contract_data['abi'])

    current_block = w3.eth.get_block_number()
    start_block = current_block - 5
    end_block = current_block

    if chain == 'source':
        event_filter = contract.events.Deposit.create_filter(fromBlock=start_block, toBlock=end_block)
        events = event_filter.get_all_entries()
        for event in events:
            handleDepositEvent(event, w3, contract_data)
    elif chain == 'destination':
        event_filter = contract.events.Unwrap.create_filter(fromBlock=start_block, toBlock=end_block)
        events = event_filter.get_all_entries()
        for event in events:
            handleUnwrapEvent(event, w3, contract_data)

def handleDepositEvent(event, w3, contract_data):
    print(f"Handling Deposit event: {event}")
    destination_contract_data = getContractInfo('destination')
    destination_w3 = connectTo(destination_chain)
    destination_contract = destination_w3.eth.contract(
        address=destination_contract_data['address'],
        abi=destination_contract_data['abi']
    )
    tx_hash = event.transactionHash.hex()
    token = event.args['token']
    recipient = event.args['recipient']
    amount = event.args['amount']

    nonce = destination_w3.eth.get_transaction_count(contract_data['address'])
    
    tx = destination_contract.functions.wrap(token, recipient, amount).build_transaction({
        'chainId': 97,
        'gas': 2000000,
        'gasPrice': destination_w3.toWei('50', 'gwei'),
        'nonce': nonce,
    })
    
    sign_and_send_transaction(destination_w3, tx)

def handleUnwrapEvent(event, w3, contract_data):
    print(f"Handling Unwrap event: {event}")
    source_contract_data = getContractInfo('source')
    source_w3 = connectTo(source_chain)
    source_contract = source_w3.eth.contract(
        address=source_contract_data['address'],
        abi=source_contract_data['abi']
    )
    tx_hash = event.transactionHash.hex()
    token = event.args['underlying_token']
    recipient = event.args['to']
    amount = event.args['amount']

    nonce = source_w3.eth.get_transaction_count(contract_data['address'])
    tx = source_contract.functions.withdraw(token, recipient, amount).buildTransaction({
        'chainId': 43113,
        'gas': 2000000,
        'gasPrice': source_w3.toWei('50', 'gwei'),
        'nonce': nonce,
    })
    sign_and_send_transaction(source_w3, tx)

def sign_and_send_transaction(w3, tx):
    p = Path(__file__).with_name('private_key.txt')
    try:
        with p.open('r') as f:
            private_key = f.read().strip()
    except Exception as e:
        print("Failed to read private key")
        print("Please contact your instructor")
        print(e)
        sys.exit(1)

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent: {tx_hash.hex()}")

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['source', 'destination']:
        print("Usage: bridge.py [source|destination]")
        sys.exit(1)

    chain = sys.argv[1]

    # Register and create tokens before scanning blocks
    if chain == 'source':
        register_and_create_tokens()

    scanBlocks(chain)