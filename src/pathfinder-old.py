import json
import math

import plotly.graph_objects as go
import requests
import web3

from hubAbi import hub_abi
from tokenAbi import token_abi


class Pathfinder:
    def __init__(self, pathfinder_url, blocknumber="latest"):
        self.w3 = web3.Web3(web3.HTTPProvider('https://rpc.circlesubi.id/'))
        self.hub = self.w3.eth.contract(address="0x29b9a7fBb8995b2423a71cC17cf9810798F6C543", abi=hub_abi)
        self.abi_token = token_abi
        self.block_number = blocknumber
        self.garden_pathfinder_URL = pathfinder_url

    def get_args_for_path(self, from_, to, value):
        token_owner = []
        print("Original token_owner:", token_owner)
        srcs = []
        dests = []
        wads = []
        query = {"method": "compute_transfer", "params": {"from": from_, "to": to, "value": str(value)}}
        response = requests.post(self.garden_pathfinder_URL, json=query)
        parsed = response.json()
        capacity = parsed["result"]["maxFlowValue"]
        for step in parsed["result"]["transferSteps"]:
            token_owner.append(web3.Web3.to_checksum_address((step["token_owner"])))
            srcs.append(web3.Web3.to_checksum_address((step["from"])))
            dests.append(web3.Web3.to_checksum_address((step["to"])))
            wads.append(int(step["value"]))
        return token_owner, srcs, dests, wads, capacity

    def get_shanky(self, tokenOwner, srcs, dests, wads):
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

    def simulate_path(self, token_owner, srcs, dests, wads, from_):
        return self.hub.functions.transferThrough(token_owner, srcs, dests, wads).call({'from': from_},
        self.block_number)

    @staticmethod
    def draw_shanky(source_, target_, value_, flow_labels, labels, colors=0):
        if colors == 0:
            colors = ["rgba(169, 169, 169,0.7)"] * len(flow_labels)

        data = [go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=["blue"] * len(flow_labels)
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
        fig.show()
