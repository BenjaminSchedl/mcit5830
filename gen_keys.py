from web3 import Web3
import eth_account
import os

def get_keys(challenge,keyId = 0, filename = "eth_mnemonic.txt"):
	"""
	Generate a stable private key
	challenge - byte string
	keyId (integer) - which key to use
	filename - filename to read and store mnemonics

	Each mnemonic is stored on a separate line
 	If fewer than (keyId+1) mnemonics have been generated, generate a new one and return that
	"""

	w3 = Web3()

	# Read existing keys from the file
	if os.path.exists(filename):
		with open(filename, 'r') as file:
            		keys = file.readlines()
	else:
		keys = []

	# Generate a new key if necessary
	if len(keys) <= keyId:
		for _ in range(len(keys), keyId + 1):
			new_account = w3.eth.account.create()
			keys.append(new_account.key.hex() + '\n')
		with open(filename, 'w') as file:
			file.writelines(keys)

	# Retrieve the key for the given keyId
	private_key = keys[keyId].strip()
	account = w3.eth.account.privateKeyToAccount(private_key)

	# Sign the challenge
	msg = eth_account.messages.encode_defunct(challenge)
	signature = w3.eth.account.sign_message(msg, private_key)

	# Verify the signature
	eth_addr = account.address

	assert eth_account.Account.recover_message(msg,signature=sig.signature.hex()) == eth_addr, f"Failed to sign message properly"

	#return sig, acct #acct contains the private key
	return sig, eth_addr

if __name__ == "__main__":
	for i in range(4):
        	challenge = os.urandom(64)
        	sig, addr= get_keys(challenge=challenge,keyId=i)
        	print( addr )
