import hashlib
from DataRecord import *


class TransactionBlock:
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        hash_data = (
            str(self.index)
            + str(self.timestamp)
            + str(self.transactions)
            + str(self.previous_hash)
            + str(self.nonce)
        )
        return hashlib.sha256(hash_data.encode()).hexdigest()

    def mine_block(self, difficulty):  # Proof of Work
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print("Block mined:", self.hash)

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data):
        block = cls(
            data["index"],
            data["timestamp"],
            [DataRecord.from_dict(tx_data) for tx_data in data["transactions"]],
            data["previous_hash"],
        )
        block.nonce = data["nonce"]
        block.hash = data["hash"]
        return block

