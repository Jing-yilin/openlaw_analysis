import random
import string
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.PublicKey import RSA
from base64 import b64encode
from Crypto.Util.Padding import pad
import math
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5

public_key = open('public.pem', 'r').read()

encrypt_pass_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz*&-%/!?*+=()"


rsakey = RSA.import_key(public_key)
def key_encrypt(data:str):
    # 生成随机的加密密钥
    pass_phrase = generate_encrypt_password(32)
    # 生成随机的iv
    iv = bytes.fromhex(''.join(random.choices(string.hexdigits, k=32)))
    # 生成随机的salt
    salt = bytes.fromhex(''.join(random.choices(string.hexdigits, k=32)))

    # 使用PBKDF2算法生成加密密钥
    key = PBKDF2(pass_phrase, salt, dkLen=16, count=1000)

    # 使用生成的密钥和iv，使用AES算法对数据data进行加密
    data = pad(data.encode('utf-8'), AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = b64encode(cipher.encrypt(data)).decode('utf-8')

    # 将密码、salt和iv拼接成字符串
    aes_key = pass_phrase + ":::" + salt.hex() + ":::" + iv.hex()

    # 将加密后的数据转换为Base64格式
    encrypted_message = encrypted_data

    # 使用RSA公钥加密AES密钥
    cipher = Cipher_pkcs1_v1_5.new(rsakey)
    encrypted_key = b64encode(cipher.encrypt(aes_key.encode('utf-8')))

    # 将加密的密钥和加密后的数据拼接成字符串并返回
    encrypted = encrypted_key.decode('utf-8') + ":::" + encrypted_message
    return encrypted


def generate_encrypt_password(length):
    random_string = ''
    for i in range(length):
        rnum = math.floor(random.random() * len(encrypt_pass_chars))
        random_string += encrypt_pass_chars[rnum:rnum+1]
    return random_string