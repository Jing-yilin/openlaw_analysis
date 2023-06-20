from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from Crypto.Protocol.KDF import PBKDF2
import base64
import random
import string

public_key = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0zI8aibR9ZN57QObFxvI
wiRTmELItVVBLMrLd71ZqakR6oWUKkcAGgmxad2TCy3UeRe4A0Dduw97oXlbl5rK
RGISzpLO8iMSYtsim5aXZX9SB5x3S9ees4CZ6MYD/4XQOTrU0r1TMT6wXlhVvwNb
fMNYHm3vkY0rhfxBCVPFJoHjAGDFWNCAhf4KfalfvWsGL32p8N/exG2S4yXVHuV6
cHDyFJAItKVmyuTmB62pnPs5KvNv6oPmtmhMxxsvBOyh7uLwB5TonxtZpWZ3A1wf
43ByuU7F3qGnFqL0GeG/JuK+ZR40LARyevHy9OZ5pMa0Nwqb8PwfK810Bc8PxD8N
EwIDAQAB
-----END PUBLIC KEY-----'''

encrypt_pass_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz*&-%/!?*+=()"

def key_encrypt(data):
    pass_phrase = generate_encrypt_password(32).encode('utf-8')
    iv = get_random_bytes(16)
    salt = get_random_bytes(16)
    key = PBKDF2(pass_phrase, salt, dkLen=16, count=1000)

    aes_cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_message = aes_cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))

    aes_key = pass_phrase.hex() + ":::" + salt.hex() + ":::" + iv.hex()
    rsa_public_key = RSA.import_key(public_key)
    cipher_rsa = PKCS1_v1_5.new(rsa_public_key)
    encrypted_key = cipher_rsa.encrypt(aes_key.encode())

    encrypted = base64.b64encode(encrypted_key).decode() + ":::" + base64.b64encode(encrypted_message).decode()
    return encrypted

def generate_encrypt_password(length):
    randomstring = ''.join(random.choice(encrypt_pass_chars) for _ in range(length))
    return randomstring