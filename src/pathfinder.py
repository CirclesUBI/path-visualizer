import argparse
import json
import math
import pprint
from collections import defaultdict

import plotly.graph_objects as go
import requests
import web3
from eth_abi import abi

from hubAbi import hub_abi
from tokenAbi import token_abi


class Pathfinder:
	def __init__(self, provider, pathfinder, blocknumber = "latest"):
		self.pathfinder = pathfinder

		if provider == "gateway":
			constr = 'https://rpc.circlesubi.id/'
		else:
			constr = provider
		self.w3 = web3.Web3(web3.HTTPProvider(constr))

		address = "0x29b9a7fBb8995b2423a71cC17cf9810798F6C543" #hub

		self.hub = self.w3.eth.contract(address=address, abi=hub_abi)
		#self.abi_token = [{"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":False,"type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":False,"type":"function"},{"inputs":[{"name":"dutchAuction","type":"address"},{"name":"owners","type":"address[]"},{"name":"tokens","type":"uint256[]"}],"payable":False,"type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"name":"from","type":"address"},{"indexed":True,"name":"to","type":"address"},{"indexed":False,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"owner","type":"address"},{"indexed":True,"name":"spender","type":"address"},{"indexed":False,"name":"value","type":"uint256"}],"name":"Approval","type":"event"}]
		self.abi_token = token_abi;
		self.blocknumber = blocknumber
		self.garden_pathfinder_URL = "http://65.109.109.165:8080/"


	def get_args(self, from_, to, value):
		if self.pathfinder == "land":
			query = {"method":"compute_transfer", "params":{"from":from_, "to": to, "value":str(value), "iterative": True, "prune": True}}
			response = requests.post(self.garden_pathfinder_URL, json=query)
			
			parsed = json.loads(response.content)			
			return parsed

	def load_safes(self):
		query = {"method":"load_safes_binary", "params":{"file":"pathfinder_binary_export_25476000.bin"}}
		response = requests.post("http://localhost:6000", json=query)

	def get_args_for_path(self, from_, to, value):

		tokenOwner = []
		srcs = []
		dests = []
		wads = []
		capacity = 0

		if self.pathfinder == "land" or self.pathfinder == "local" or self.pathfinder == "static":
			if self.pathfinder == "static":
				with open('path.json', 'r') as f:
					parsed = json.load(f)
					for step in parsed["transfers"]:
						tokenOwner.append(web3.Web3.to_checksum_address((step["tokenOwner"])))
						srcs.append(web3.Web3.to_checksum_address((step["from"])))
						dests.append(web3.Web3.to_checksum_address((step["to"])))
						wads.append(int(step["value"]))
			else:
				query = {"method":"compute_transfer", "params":{"from":from_, "to": to, "value":str(value)}}
				url = self.garden_pathfinder_URL
				if self.pathfinder == "local":
					url = "http://localhost:6000"
				response = requests.post(url, json=query)
				#pprint.pprint(response.content)
				parsed = json.loads(response.content)
				#pprint.pprint(parsed)

				capacity = parsed["result"]["maxFlowValue"]
				for step in parsed["result"]["transferSteps"]:
					tokenOwner.append(web3.Web3.to_checksum_address((step["token_owner"])))
					srcs.append(web3.Web3.to_checksum_address((step["from"])))
					dests.append(web3.Web3.to_checksum_address((step["to"])))
					wads.append(int(step["value"]))

		else:

			query = {"from":from_, "to": to, "value":str(value)}
			response = requests.post("https://api.circles.garden/api/transfers/", json=query)
			parsed = json.loads(response.content)
			#pprint.pprint(parsed)
			for step in parsed["data"]["transferSteps"]:
				tokenOwner.append(web3.Web3.to_checksum_address((step["tokenOwnerAddress"])))
				srcs.append(web3.Web3.to_checksum_address((step["from"])))
				dests.append(web3.Web3.to_checksum_address((step["to"])))
				wads.append(int(step["value"]))


		return tokenOwner, srcs, dests, wads, capacity

	def get_args_from_tx_hash(self, txhash):
		tx = self.w3.eth.get_transaction(txhash)
		DATA = tx.data[10:]
		DATA = bytes.fromhex(DATA)


		abi_ = ["address", "uint256", "bytes", "uint8", "uint256", "uint256", "uint256", "address", "address", "bytes"]
		decodedABI = abi.decode(abi_, DATA)
		decodedABI = bytes.fromhex(decodedABI[2].hex()[8:])


		abi_ = ["address[]", "address[]", "address[]", "uint256[]"]
		decodedABI = abi.decode(abi_, decodedABI)
		return list(decodedABI[0]),list(decodedABI[1]),list(decodedABI[2]),list(decodedABI[3])


	def get_shanky(self, tokenOwner, srcs, dests, wads):

		address_index_map = {}
		safe_list = []
		j = 0
		for i in range(len(srcs)):
			if (not srcs[i] in address_index_map.keys()):
				address_index_map[srcs[i]] = j
				safe_list.append(srcs[i])
				j += 1

		for i in range(len(dests)):
			if (not dests[i] in address_index_map.keys()):
				address_index_map[dests[i]] = j
				safe_list.append(dests[i])
				j += 1

		#print(address_index_map)

		source_ = []
		target_ = []
		value_ = []
		for i in range(len(srcs)):
			source_.append(address_index_map[srcs[i]])
			target_.append(address_index_map[dests[i]])
			value_.append(wads[i] / 10 ** 18)
		
		lables = self.get_names(safe_list)
		flow_lables = self.get_names(tokenOwner)
		flow_lables = [i + " CRC" for i in flow_lables]
		#self.is_frozen(safe_list)
		return source_,target_,value_,flow_lables, lables


	def get_balance(self, guy, tokenOwner):
		guy = web3.Web3.to_checksum_address(guy)
		tokenOwner = web3.Web3.to_checksum_address(tokenOwner)
		tokenaddress = self.hub.functions.userToToken(tokenOwner).call({}, self.blocknumber)
		token = self.w3.eth.contract(address = tokenaddress, abi=self.abi_token)
		try:
			return token.functions.balanceOf(guy).call({}, self.blocknumber)
		except:
			print("Error in getting balance of guy, token, token O.: " + str(guy) + " " + str(tokenaddress) + " " + str(tokenOwner))
			return 0

	def is_frozen(self, safes):
		safes = [web3.Web3.to_checksum_address(i) for i in safes]
		return_list = []
		for safe in safes:
			tokenaddress = self.hub.functions.userToToken(safe).call({}, self.blocknumber)
			if tokenaddress != "0x0000000000000000000000000000000000000000":
				token = self.w3.eth.contract(address = tokenaddress, abi=self.abi_token)
				try:
					stopped = token.functions.stopped().call({}, self.blocknumber)
					return_list.append((safe, stopped))
				except:
					print("Error in getting stopped of safe, token: " + str(safe) + " " + str(tokenaddress))
		pprint.pprint(return_list)

	def get_receive_capacity(self, receiver, token, own_tokens_received = 0):
		if self.hub.functions.organizations(receiver).call({}, self.blocknumber) or token == receiver:
			return 100000 * 10**18
		own_token = self.get_balance(receiver, receiver)
		receiver_token = self.get_balance(receiver, token)
		trustlimit = self.hub.functions.limits(receiver, token).call({}, self.blocknumber)

		return (own_token + own_tokens_received) * (trustlimit/100) - receiver_token
		
	def aggregate_token_flows(self, tokenOwner, srcs, dests, wads):
		flows = []
		dd = defaultdict(lambda: defaultdict(int))
		for i in range(len(tokenOwner)):
			dd[dests[i]][tokenOwner[i]] += wads[i]

		for receiver, sends in dd.items():
			own_token_wad = sends[receiver]
			for token, wads in sends.items():
				cap = self.get_receive_capacity(receiver, token, own_token_wad)
				if wads > cap:
					names = self.get_names([receiver, token])
					print("Problem with sending " + names[1] + " tokens to " + names[0])
					print("capacity = " + str(cap / 10**18) + " total send:" + str(wads / 10**18))
					print(str(wads), " ", str(cap))


	def get_send_limits(self, tokenOwner, src, dest):

		tokenOwner = web3.Web3.to_checksum_address(tokenOwner)
		src = web3.Web3.to_checksum_address(src)
		dest = web3.Web3.to_checksum_address(dest)


		return self.hub.functions.checkSendLimit(tokenOwner, src, dest).call({}, self.blocknumber)

	def debug_ttransfer(self, tokenOwner, srcs, dests, wads):
		colors = []
		for i in range(len(tokenOwner)):
			try:
				self.simulate_path(tokenOwner[i:i+1], srcs[i:i+1], dests[i:i+1], wads[i:i+1], srcs[i])
				#print("debug worked hop:" + str(i))
				colors.append("rgba(169, 169, 169,0.7)")
			except:
				print("an exception occured in debug:")
				colors.append("rgba(256, 0, 0,0.8)")
				names = self.get_names([tokenOwner[i], srcs[i], dests[i]])
				print("token Owner: " + names[0] + str(tokenOwner[i:i+1]))
				print("src: " + names[1] + str(srcs[i:i+1]))
				print("dest: " + names[2] + str(dests[i:i+1]))
				print(wads[i:i+1])
				print("from: " + str(srcs[i:i+1]))
				print("balance: " + str(self.get_balance(srcs[i], tokenOwner[i])/ 10 ** 18 ))
				print("capacity: " + str(self.get_receive_capacity(dests[i], tokenOwner[i]) / 10 ** 18 ))
				print("checkSendLimit: " + str(self.get_send_limits(tokenOwner[i], srcs[i], dests[i])))
				print("amount: " + str(wads[i] / 10**18))
		return colors

	def get_names(self, safes):
		safes = [web3.Web3.to_checksum_address(i) for i in safes]
		return_list = safes.copy()
		bulk = 100
		for k in range(math.ceil((len(safes)/bulk))):

			current = safes[k*bulk:(k+1)*bulk]

			query = "?"
			for i in current:
				query = query + "address[]=" +i + "&"
			query = "https://api.circles.garden/api/users/" + query
			
			response = requests.get(query)
			parsed = json.loads(response.content)
			
			for i in parsed['data']:
				for j in range(len(current)):
					if current[j] == i["safeAddress"]:
						return_list[j + k*bulk] = i["username"]
		return return_list

	def sort_args(self, tokenOwner, srcs, dests, wads):
		tokenOwner_ = []
		srcs_ = []
		dests_ = []
		wads_ = []


		for i in range(len(tokenOwner)):
			if tokenOwner[i] != dests[i] and tokenOwner[i] != srcs[i]:
				tokenOwner_.append(tokenOwner[i])
				srcs_.append(srcs[i])
				dests_.append(dests[i])
				wads_.append(wads[i])


		for i in range(len(tokenOwner)):
			if tokenOwner[i] == srcs[i]:
				tokenOwner_.append(tokenOwner[i])
				srcs_.append(srcs[i])
				dests_.append(dests[i])
				wads_.append(wads[i])
			elif tokenOwner[i] == dests[i]:
				tokenOwner_.insert(0,tokenOwner[i])
				srcs_.insert(0,srcs[i])
				dests_.insert(0,dests[i])
				wads_.insert(0,wads[i])
		return tokenOwner_, srcs_, dests_, wads_
			
	def simulate_path(self, tokenOwner, srcs, dests, wads, from_):

		return self.hub.functions.transferThrough(tokenOwner, srcs, dests, wads).call({'from': from_}, self.blocknumber)

	def draw_shanky(self, source_, target_, value_, flow_lables, lables, colors=0):

		if colors == 0:
			colors = ["rgba(169, 169, 169,0.7)"]*len(flow_lables)

		data =[go.Sankey(
			node = dict(
			  pad = 15,
			  thickness = 20,
			  line = dict(color = "black", width = 0.5),
			  label = lables,
			  color = ["blue"]*len(flow_lables)
			),
			link = dict(
			  source = source_,
			  target = target_,
			  value = value_,
			  label = flow_lables,
			  color = colors
		  ))]

		
		# change 'magenta' to its 'rgba' value to add opacity
		#data[0]['node']['color'] = ['rgba(255,0,255, 0.8)' if color == "magenta" else color for color in data[0]['node']['color']]
		#data[0]['link']['color'] = [data[0]['link']['color'][src].replace("0.8", str(opacity)) for src in data[0]['link']['source']]

		fig = go.Figure(data)

		fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
		fig.show()

	def draw_shanky_from_tx_hash(self, txhash):
		args = self.get_args_from_tx_hash(txhash)
		shanky = self.get_shanky(*args)
		self.draw_shanky(*shanky)
