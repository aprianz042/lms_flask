import hashlib

def md5_hash(password):
    return hashlib.md5(password.encode()).hexdigest()