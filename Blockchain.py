import time
from TransactionBlock import *

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 4
        self.pending_transactions = []
        self.auction_items = {}

    def create_genesis_block(self):
        return TransactionBlock(0, time.time(), [], "0")

    @property
    def latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self):
        print("PENDING TRANSACTIONS:", len(self.pending_transactions))
        block = TransactionBlock(
            len(self.chain),
            time.time(),
            self.pending_transactions,
            self.latest_block.hash,
        )
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def create_auction_item(self, item_id, item_name, initial_price):
        self.auction_items[item_id] = {
            "item_name": item_name,
            "initial_price": initial_price,
            "bids": [],
        }

    def place_bid(self, bidder_wallet, item_id, bid_amount):
        if item_id in self.auction_items:
            item = self.auction_items[item_id]
            bid = {
                "bidder": bidder_wallet.get_public_key_bytes(),
                "amount": bid_amount,
            }
            self.add_transaction(
                DataRecord(
                    bidder_wallet.get_public_key_bytes(), item_id.encode(), bid_amount
                )
            )
            item["bids"].append(bid)
        else:
            print("Invalid item ID")

    def get_item_bids(self, item_id):
        if item_id in self.auction_items:
            item = self.auction_items[item_id]
            return item["bids"]
        else:
            return []

    def get_item_winner(self, item_id):
        if item_id in self.auction_items:
            item = self.auction_items[item_id]
            if item["bids"]:
                sorted_bids = sorted(
                    item["bids"], key=lambda x: x["amount"], reverse=True
                )
                winner = sorted_bids[0]["bidder"]
                return winner
            else:
                return None
        else:
            return None
