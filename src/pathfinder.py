import json
import math
import os
import plotly.graph_objects as go
import requests
import web3
import subprocess

from dotenv import load_dotenv
from hubAbi import hub_abi
from tokenAbi import token_abi

load_dotenv()
class Pathfinder:
    def __init__(self, pathfinder_url=None, blocknumber="latest"):
        self.pathfinder_url = pathfinder_url or os.getenv('PATHFINDER_URL')
        circles_hub_contract = os.getenv('CIRCLES_HUB_CONTRACT')
        web3_http_provider_url = os.getenv('CIRCLES_RPC_URL')
        self.w3 = web3.Web3(web3.HTTPProvider(web3_http_provider_url))
        self.hub = self.w3.eth.contract(address=circles_hub_contract, abi=hub_abi)
        self.abi_token = token_abi
        self.block_number = blocknumber
        self.garden_pathfinder_URL = self.pathfinder_url 

    def get_args_for_path(self, from_, to, value):
        token_owner = []
        srcs = []
        dests = []
        wads = []
        query = {"method": "compute_transfer", "params": {"from": from_, "to": to, "value": str(value)}}
        response = requests.post(self.garden_pathfinder_URL, json=query)
        
        # Step 1: Inspect the API response
        if response.status_code == 200:
            parsed = response.json()
            print(parsed)  # Add this line to inspect the structure of the response
        else:
            print(f"Error calling API: {response.status_code}")
            return [], [], [], [], 0  # Handle the error by returning empty lists and 0 capacity

        # Step 2 and 3: Check for the 'result' key and handle possible errors or different structures
        if 'result' in parsed:
            capacity = parsed["result"]["maxFlowValue"]
            for step in parsed["result"]["transferSteps"]:
                token_owner.append(web3.Web3.to_checksum_address((step["token_owner"])))
                srcs.append(web3.Web3.to_checksum_address((step["from"])))
                dests.append(web3.Web3.to_checksum_address((step["to"])))
                wads.append(int(step["value"]))
            return token_owner, srcs, dests, wads, capacity
        else:
            # Handle the case where 'result' is not in the response
            print("Error or unexpected response structure:", parsed)
            return [], [], [], [], 0

    def get_sankey(self, tokenOwner, srcs, dests, wads):
        address_index_map = {}
        safe_list = []
        j = 0
        for i in range(len(srcs)):
            if not srcs[i] in address_index_map.keys():
                address_index_map[srcs[i]] = j
                safe_list.append(srcs[i])
                j += 1

        for i in range(len(dests)):
            if not dests[i] in address_index_map.keys():
                address_index_map[dests[i]] = j
                safe_list.append(dests[i])
                j += 1

        source_ = []
        target_ = []
        value_ = []
        for i in range(len(srcs)):
            source_.append(address_index_map[srcs[i]])
            target_.append(address_index_map[dests[i]])
            value_.append(wads[i] / 10 ** 18)

        labels = self.get_names(safe_list)
        flow_labels = self.get_names(tokenOwner)
        flow_labels = [i + " CRC" for i in flow_labels]

        return source_, target_, value_, flow_labels, labels

    @staticmethod
    def get_names(safes):
        safes = [web3.Web3.to_checksum_address(i) for i in safes]
        return_list = safes.copy()
        bulk = 100
        for k in range(math.ceil((len(safes) / bulk))):

            current = safes[k * bulk:(k + 1) * bulk]

            query = "?"
            for i in current:
                query = query + "address[]=" + i + "&"
            query = "https://api.circles.garden/api/users/" + query

            response = requests.get(query)
            parsed = json.loads(response.content)

            for i in parsed['data']:
                for j in range(len(current)):
                    if current[j] == i["safeAddress"]:
                        return_list[j + k * bulk] = i["username"]
        return return_list

    @staticmethod
    def sort_args(token_owner, srcs, dests, wads):
        tokenOwner_ = []
        srcs_ = []
        dests_ = []
        wads_ = []

        for i in range(len(token_owner)):
            if token_owner[i] != dests[i] and token_owner[i] != srcs[i]:
                tokenOwner_.append(token_owner[i])
                srcs_.append(srcs[i])
                dests_.append(dests[i])
                wads_.append(wads[i])

        for i in range(len(token_owner)):
            if token_owner[i] == srcs[i]:
                tokenOwner_.append(token_owner[i])
                srcs_.append(srcs[i])
                dests_.append(dests[i])
                wads_.append(wads[i])
            elif token_owner[i] == dests[i]:
                tokenOwner_.insert(0, token_owner[i])
                srcs_.insert(0, srcs[i])
                dests_.insert(0, dests[i])
                wads_.insert(0, wads[i])
        return tokenOwner_, srcs_, dests_, wads_

    
    def fetch_trust_connections(self, address):
        script_path = 'circlesSdk.js'
        result = subprocess.run(['node', script_path, address], capture_output=True, text=True)

        if result.stderr:
            print("Error calling Circles SDK script:", result.stderr)

        try:
            trust_connections = json.loads(result.stdout)
            if trust_connections:
                print(trust_connections)
                return trust_connections
            else:
                print("No trust connections found.")
                return []
        except json.JSONDecodeError as e:
            print("Error parsing JSON output:", e)
            return None
        except Exception as e:
            print("An unexpected error occurred:", e)
            return None 


    def process_data_for_visualization(self, trust_connections, avatar_address):
        nodes = [{'id': avatar_address}]
        links = []

        for connection in trust_connections:
            nodes.append({'id': connection['address']})
            links.append({
                'source': avatar_address,
                'target': connection['address'],
                'value': connection['limit']
            })

        return nodes, links

    def resolve_username_to_address(self, username):
        query_url = f"https://api.circles.garden/api/users/?username[]={username}"
        response = requests.get(query_url)
        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                for user in data["data"]:
                    if "safeAddress" in user:
                        return user["safeAddress"]
        return None

    def draw_sankey(self, source_, target_, value_, flow_labels, labels, colors=None):
        if colors is None:
            colors = ["rgba(169, 169, 169,0.7)"] * len(flow_labels)

        data = [go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=["blue"] * len(labels)
            ),
            link=dict(
                source=source_,
                target=target_,
                value=value_,
                label=flow_labels,
                color=colors
            ))]

        fig = go.Figure(data)
        fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
        return fig
