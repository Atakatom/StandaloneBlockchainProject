from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

class DataRecord:
    def __init__(self, sender, recipient, amount, signature=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

    def sign_transaction(self, private_key):
        data = self.sender + self.recipient + str(self.amount).encode()
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        self.signature = signature

    def verify_transaction(self, public_key):
        try:
            public_key.verify(
                self.signature,
                self.sender + self.recipient + str(self.amount).encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False

    def to_dict(self):
        return {
            "sender": self.sender.decode(),
            "recipient": self.recipient.decode(),
            "amount": self.amount,
            "signature": self.signature.hex(),  # Convert bytes to hexadecimal string
        }

    @classmethod
    def from_dict(cls, data):
        sender = data["sender"].encode()
        recipient = data["recipient"].encode()
        amount = data["amount"]
        signature = bytes.fromhex(
            data["signature"]
        )  # Convert hexadecimal string to bytes
        return cls(sender, recipient, amount, signature)
