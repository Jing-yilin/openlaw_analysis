import execjs
import pathlib
import sys


def js_from_file(file_name):
    """
    读取js文件
    :return:
    """
    with open(file_name, 'r', encoding='UTF-8') as file:
        result = file.read()

    return result

def encrypt_js(password):
    # 编译加载js字符串
    context = execjs.compile(js_from_file(
        str(pathlib.Path(__file__).resolve().parent) + "/encrypt.js"
    ))
    encrypted_pwd = context.call("keyEncrypt", password)
    return encrypted_pwd

# main
if __name__ == "__main__":
    password = "123456"
    print(encrypt_js(password))