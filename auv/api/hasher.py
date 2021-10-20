"""
Hasher file for checksum communication validation.
"""
import hashlib


class Hasher():
    def __init__(self):
        pass

    def checksum(self, msg, val):
        return self.generate_hash(msg) == val

    def generate_hash(self, msg):
        return hashlib.sha256(msg.encode('utf-8'))
