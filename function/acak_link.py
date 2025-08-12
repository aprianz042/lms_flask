from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os

def encrypt(plain_text):
    key = "MySecretKey123!"
    cipher = AES.new(key, AES.MODE_CBC)  # CBC mode
    ct_bytes = cipher.encrypt(pad(plain_text.encode(), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv + ":" + ct  # Combine IV and ciphertext

def decrypt(encrypted_text):
    key = "MySecretKey123!"
    iv, ct = encrypted_text.split(":")
    iv = base64.b64decode(iv)
    ct = base64.b64decode(ct)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')
    return pt

