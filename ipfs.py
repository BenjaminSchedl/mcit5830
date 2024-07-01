import requests
import json

PINATA_API_KEY = '7833a774d384feb68fde'
PINATA_SECRET_API_KEY = '414ebb46e5c875886cc4dd177bf9edce09d3b857bc0f289b40c3b0b3036c29fe'
PINATA_API_URL = 'https://api.pinata.cloud'

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"

	json_data = json.dumps(data)

	response = requests.post(
		f"{PINATA_API_URL}/pinning/pinJSONToIPFS",
		headers={
			"pinata_api_key": PINATA_API_KEY,
			"pinata_secret_api_key": PINATA_SECRET_API_KEY
		},
		json={
			"pinataContent": data
		}
	)
	cid = response.json()["IpfsHash"]

	return cid

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	
	url = f"https://gateway.pinata.cloud/ipfs/{cid}"

	response = requests.get(url)

	data = response.json()

	assert isinstance(data,dict), f"get_from_ipfs should return a dict"
	return data
