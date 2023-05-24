import json
import math
import pprint

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

    def get_args(self, from_, to, value):
        query = {"method": "compute_transfer",
                 "params": {"from": from_, "to": to, "value": str(value), "iterative": True, "prune": True}}
        response = requests.post(self.garden_pathfinder_URL, json=query)
        return json.loads(response.content)

    def get_args_for_path(self, from_, to, value):
        token_owner = []
        srcs = []
        dests = []
        wads = []
        query = {"method": "compute_transfer", "params": {"from": from_, "to": to, "value": str(value)}}
        response = requests.post(self.garden_pathfinder_URL, json=query)
        parsed = json.loads(response.content)
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
            if (not srcs[i] in address_index_map.keys()):
                address_index_map[srcs[i]] = j
                safe_list.append(srcs[i])
                j += 1

        for i in range(len(dests)):
            if (not dests[i] in address_index_map.keys()):
                address_index_map[dests[i]] = j
                safe_list.append(dests[i])
                j += 1

        # print(address_index_map)

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
        # self.is_frozen(safe_list)
        return source_, target_, value_, flow_labels, labels

    def get_balance(self, guy, token_owner):
        guy = web3.Web3.to_checksum_address(guy)
        token_owner = web3.Web3.to_checksum_address(token_owner)
        token_address = self.hub.functions.userToToken(token_owner).call({}, self.block_number)
        token = self.w3.eth.contract(address=token_address, abi=self.abi_token)
        try:
            return token.functions.balanceOf(guy).call({}, self.block_number)
        except:
            print("Error in getting balance of guy, token, token O.: " + str(guy) + " " + str(token_address) + " " + str(
                token_owner))
            return 0

    def is_frozen(self, safes):
        safes = [web3.Web3.to_checksum_address(i) for i in safes]
        return_list = []
        for safe in safes:
            token_address = self.hub.functions.userToToken(safe).call({}, self.block_number)
            if token_address != "0x0000000000000000000000000000000000000000":
                token = self.w3.eth.contract(address=token_address, abi=self.abi_token)
                try:
                    stopped = token.functions.stopped().call({}, self.block_number)
                    return_list.append((safe, stopped))
                except:
                    print("Error in getting stopped of safe, token: " + str(safe) + " " + str(token_address))
        pprint.pprint(return_list)

    def get_receive_capacity(self, receiver, token, own_tokens_received=0):
        if self.hub.functions.organizations(receiver).call({}, self.block_number) or token == receiver:
            return 100000 * 10 ** 18
        own_token = self.get_balance(receiver, receiver)
        receiver_token = self.get_balance(receiver, token)
        trust_limit = self.hub.functions.limits(receiver, token).call({}, self.block_number)

        return (own_token + own_tokens_received) * (trust_limit / 100) - receiver_token

    def get_send_limits(self, token_owner, src, dest):
        token_owner = web3.Web3.to_checksum_address(token_owner)
        src = web3.Web3.to_checksum_address(src)
        dest = web3.Web3.to_checksum_address(dest)

        return self.hub.functions.checkSendLimit(token_owner, src, dest).call({}, self.block_number)

    def debug_transfer(self, token_owner, srcs, dests, wads):
        colors = []
        for i in range(len(token_owner)):
            try:
                self.simulate_path(token_owner[i:i + 1], srcs[i:i + 1], dests[i:i + 1], wads[i:i + 1], srcs[i])
                # print("debug worked hop:" + str(i))
                colors.append("rgba(169, 169, 169,0.7)")
            except:
                print("an exception occured in debug:")
                colors.append("rgba(256, 0, 0,0.8)")
                names = self.get_names([token_owner[i], srcs[i], dests[i]])
                print("token Owner: " + names[0] + str(token_owner[i:i + 1]))
                print("src: " + names[1] + str(srcs[i:i + 1]))
                print("dest: " + names[2] + str(dests[i:i + 1]))
                print(wads[i:i + 1])
                print("from: " + str(srcs[i:i + 1]))
                print("balance: " + str(self.get_balance(srcs[i], token_owner[i]) / 10 ** 18))
                print("capacity: " + str(self.get_receive_capacity(dests[i], token_owner[i]) / 10 ** 18))
                print("checkSendLimit: " + str(self.get_send_limits(token_owner[i], srcs[i], dests[i])))
                print("amount: " + str(wads[i] / 10 ** 18))
        return colors

    def get_names(self, safes):
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

    def sort_args(self, token_owner, srcs, dests, wads):
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

    def draw_shanky(self, source_, target_, value_, flow_labels, labels, colors=0):
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
