import json
import threading
import socket
import time

from App import DigitalWallet

class PeerNode:
    def __init__(self, host, port, blockchain):
        self.host = host
        self.port = port
        self.node_id = f"{self.host}:{self.port}"
        self.blockchain = blockchain
        self.server = None
        self.peers = set()

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f"Node {self.node_id} listening on {self.host}:{self.port}")
        threading.Thread(target=self.accept_connections).start()
        threading.Thread(target=self.discover_peers).start()

    def accept_connections(self):
        while True:
            client_socket, client_address = self.server.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            threading.Thread(target=self.handle_peer, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        request = self.receive_message(client_socket)
        if request:
            message_type = request["type"]
            if message_type == "create_auction_item":
                item_id = request["data"]["item_id"]
                item_name = request["data"]["item_name"]
                initial_price = request["data"]["initial_price"]
                self.blockchain.create_auction_item(item_id, item_name, initial_price)
                response = {"type": "auction_item_created"}
                self.send_message(client_socket, response)
            elif message_type == "place_bid":
                bidder_wallet = request["data"]["bidder_wallet"]
                item_id = request["data"]["item_id"]
                bid_amount = request["data"]["bid_amount"]
                bidder_wallet = bytes.fromhex(bidder_wallet)
                bidder_wallet = DigitalWallet.from_dict(bidder_wallet)
                self.blockchain.place_bid(bidder_wallet, item_id, bid_amount)
                response = {"type": "bid_placed"}
                self.send_message(client_socket, response)
            elif message_type == "get_item_bids":
                item_id = request["data"]["item_id"]
                bids = self.blockchain.get_item_bids(item_id)
                response = {"type": "item_bids_response", "data": {"bids": bids}}
                self.send_message(client_socket, response)
            elif message_type == "get_item_winner":
                item_id = request["data"]["item_id"]
                winner = self.blockchain.get_item_winner(item_id)
                response = {"type": "item_winner_response", "data": {"winner": winner}}
                self.send_message(client_socket, response)
            else:
                response = {"type": "error", "message": "Invalid message type"}
                self.send_message(client_socket, response)
        client_socket.close()

    def send_message(self, client_socket, message):
        data = self.serialize_message(message)
        client_socket.sendall(data)

    def receive_message(self, client_socket):
        complete_data = b""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            complete_data += data

            if len(complete_data) >= 4:
                message_length = int.from_bytes(complete_data[:4], "big")
                if len(complete_data) >= 4 + message_length:
                    message_data = complete_data[4 : 4 + message_length]
                    message = self.deserialize_message(message_data)
                    return message

        return None

    @staticmethod
    def serialize_message(message):
        return json.dumps(message).encode()

    @staticmethod
    def deserialize_message(data):
        return json.loads(data.decode())

    def connect_to_peer(self, peer_host, peer_port):
        if (peer_host, peer_port) not in self.peers:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_host, peer_port))
                self.peers.add((peer_host, peer_port))
                threading.Thread(target=self.handle_peer, args=(peer_socket,)).start()
                print(f"Connected to peer {peer_host}:{peer_port}")
                self.send_message(peer_socket, {"type": "get_blockchain"})
            except ConnectionRefusedError:
                print(f"Connection to peer {peer_host}:{peer_port} refused")

    def handle_peer(self, peer_socket):
        request = self.receive_message(peer_socket)
        if request:
            message_type = request["type"]
            if message_type == "get_peers":
                response = {
                    "type": "peers_response",
                    "data": {"peers": list(self.peers)},
                }
                self.send_message(peer_socket, response)
            elif message_type == "add_peer":
                peer_host = request["data"]["host"]
                peer_port = request["data"]["port"]
                self.connect_to_peer(peer_host, peer_port)
            elif message_type == "blockchain_response":
                received_blockchain = request["data"]["blockchain"]
                if len(received_blockchain) > len(self.blockchain.chain):
                    self.blockchain.chain = [
                        DigitalWallet.from_dict(block_data)
                        for block_data in received_blockchain
                    ]
                    print("Updated blockchain received from peer")
            elif message_type == "new_block":
                block_data = request["data"]
                block = DigitalWallet.from_dict(block_data)
                if block.index == self.blockchain.latest_block.index + 1:
                    self.blockchain.chain.append(block)
                    print("New block added to the blockchain")
                else:
                    print("Received block has incorrect index")
            else:
                response = {"type": "error", "message": "Invalid message type"}
                self.send_message(peer_socket, response)
        peer_socket.close()

    def broadcast_message(self, message):
        for peer_host, peer_port in self.peers:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_host, peer_port))
                self.send_message(peer_socket, message)
                peer_socket.close()
            except ConnectionRefusedError:
                print(f"Connection to peer {peer_host}:{peer_port} refused")

    def start_mining(self, difficulty):
        while True:
            self.blockchain.mine_pending_transactions()
            block = self.blockchain.latest_block
            message = {"type": "new_block", "data": block.to_dict()}
            self.broadcast_message(message)
            time.sleep(5)  # Mine a new block every 5 seconds

    def discover_peers(self):
        while True:
            for peer_host, peer_port in self.peers.copy():
                try:
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_socket.connect((peer_host, peer_port))
                    self.send_message(peer_socket, {"type": "get_peers"})
                    response = self.receive_message(peer_socket)
                    if response and response["type"] == "peers_response":
                        new_peers = response["data"]["peers"]
                        for new_peer in new_peers:
                            if (
                                new_peer != (self.host, self.port)
                                and new_peer not in self.peers
                            ):
                                self.peers.add(new_peer)
                                self.send_message(
                                    peer_socket,
                                    {
                                        "type": "add_peer",
                                        "data": {"host": self.host, "port": self.port},
                                    },
                                )
                    peer_socket.close()
                except ConnectionRefusedError:
                    print(f"Connection to peer {peer_host}:{peer_port} refused")
            time.sleep(30)  # Discover peers every 30 seconds

