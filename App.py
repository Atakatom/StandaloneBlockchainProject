import time
import threading

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from Blockchain import *
from DataRecord import *
from PeerNode import *

def public_key_to_bytes(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

def bytes_to_public_key(public_key_bytes):
    return serialization.load_pem_public_key(
        public_key_bytes,
        backend=default_backend(),
    )

class DigitalWallet:
    def __init__(self):
        self.private_key, self.public_key = self.generate_keys()

    def generate_keys(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        public_key = private_key.public_key()
        return private_key, public_key

    def sign_transaction(self, transaction):
        transaction.sign_transaction(self.private_key)

    def get_public_key_bytes(self):
        return public_key_to_bytes(self.public_key)

def main():
    # Create a blockchain instance
    blockchain = Blockchain()

    # Create a node and start it
    node = PeerNode("localhost", 5000, blockchain)
    node.start()

    # Create a node and start it
    bootstrap_node = PeerNode("localhost", 5001, blockchain)
    bootstrap_node.start()

    # Connect tothe bootstrap node
    node.connect_to_peer("localhost", 5001)

    # Start mining thread
    threading.Thread(target=node.start_mining, args=(blockchain.difficulty,)).start()

    # Create auction items
    node.blockchain.create_auction_item("item1", "Item 1", 100)
    node.blockchain.create_auction_item("item2", "Item 2", 200)

    # Create wallets for bidders
    bidder1 = DigitalWallet()
    bidder2 = DigitalWallet()

    # Place bids
    node.blockchain.place_bid(bidder1, "item1", 120)
    node.blockchain.place_bid(bidder2, "item1", 150)
    node.blockchain.place_bid(bidder2, "item2", 250)

    # Get item bids
    item1_bids = node.blockchain.get_item_bids("item1")
    item2_bids = node.blockchain.get_item_bids("item2")

    print("Item 1 Bids:")
    for bid in item1_bids:
        print(f"Bidder: {bid['bidder']}, Amount: {bid['amount']}")
    print("Item 2 Bids:")
    for bid in item2_bids:
        print(f"Bidder: {bid['bidder']}, Amount: {bid['amount']}")

    # Get item winners
    item1_winner = node.blockchain.get_item_winner("item1")
    item2_winner = node.blockchain.get_item_winner("item2")

    print("Item 1 Winner:", item1_winner)
    print("Item 2 Winner:", item2_winner)

    # Wait for mining thread to complete
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
