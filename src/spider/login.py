import aiohttp
import asyncio
import re
import pathlib
import sys
import yaml

sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))

from utils import encrypt_js, create_dir

async def new_login_openlaw(username:str, password:str, session: aiohttp.ClientSession) -> str:
    all_user_data_path = str(pathlib.Path(__file__).parent.parent.parent.absolute()) + "/data/all_user_data"
    user_data_file = all_user_data_path + "/" + username + ".yaml"
    create_dir(all_user_data_path)

    # 1. 在登录页提交get请求
    url = "http://openlaw.cn/login.jsp"
    headers = {
        "Host": "openlaw.cn",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", 
        "Accept-Language": "en-US,en;q=0.5", 
        "Accept-Encoding": "gzip, deflate", 
        "Referer": "http://openlaw.cn/login.jsp", 
        "DNT": "1", 
        "Connection": "keep-alive", 
        "Upgrade-Insecure-Requests": "1", 
        "Sec-GPC": "1", 
        "Pragma": "no-cache", 
        "Cache-Control": "no-cache"
    }
    print(f"\n开始提交get请求至 {url}")
    async with session.get(url, headers=headers) as resp:
        if not resp.status == 200:
            print(f"[{resp.status} ERROR] 无法访问: {url}")
            return
        print(f"[200 OK] 成功访问: {url}")
        text = await resp.text()
        csrf = re.findall(r'<input type="hidden" name="_csrf" value="(.*)"/>', text)[0]
        cookie_session = resp.cookies.get("SESSION").value
        print(f"SESSION = {cookie_session}")
        # 加密
        encrypted_password = encrypt_js(password)
    

    # 2. 在登录页提交post请求
    url = "http://openlaw.cn/login"
    headers = {
            "Host": "openlaw.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", 
            "Accept-Language": "en-US,en;q=0.5", 
            "Accept-Encoding": "gzip, deflate", 
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "518",
            "Origin": "http://openlaw.cn",
            "DNT": "1", 
            "Connection": "keep-alive", 
            "Referer": "http://openlaw.cn/login.jsp", 
            "Cookie": f"SESSION={cookie_session}", 
            "Upgrade-Insecure-Requests": "1", 
            "Sec-GPC": "1"
        }
    data = {
        "_csrf": csrf,
        "username": username,
        "password": encrypted_password,
        "_spring_security_remember_me": "true"
    }
    print(f"\n开始提交post请求至{url}")
    print(f"\nheaders = {headers}")
    async with session.post(url, headers=headers, data=data) as resp:
        if not resp.status == 200:
            print(f"[{resp.status} ERROR] 无法访问: {url}")
            return
        print(f"[200 OK] 成功访问: {url}")

    # 保存session到用户文件
    with open(user_data_file, "w") as f:
        yaml.dump({"cookie_session": cookie_session}, f)

    return "SESSION=" + cookie_session


async def login_openlaw(username:str, password:str, session: aiohttp.ClientSession) -> str:
    all_user_data_path = str(pathlib.Path(__file__).parent.parent.parent.absolute()) + "/data/all_user_data"
    user_data_file = all_user_data_path + "/" + username + ".yaml"

    try:
        # 读取旧的session
        with open(user_data_file, "r") as f:
            user_data = yaml.load(f, Loader=yaml.FullLoader)
            cookie_session = user_data["cookie_session"]
            print(f"读取到旧的cookie_session: {cookie_session}")

        # 尝试使用旧的session登录
        url = "http://openlaw.cn/"
        headers = {
            "Host": "openlaw.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", 
            "Accept-Language": "en-US,en;q=0.5", 
            "Accept-Encoding": "gzip, deflate", 
            "DNT": "1", 
            "Connection": "keep-alive", 
            "Cookie": f"SESSION={cookie_session}", 
            "Upgrade-Insecure-Requests": "1", 
            "Sec-GPC": "1", 
            "Pragma": "no-cache", 
            "Cache-Control": "no-cache"
        }

        print(f"\n开始提交get请求至 {url}")
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                print("[200 OK] 可是使用保存的cookie")
                return "SESSION=" + cookie_session
            else:
                print(f"[{resp.status} ERROR] 无法访问: {url}")
                return await new_login_openlaw(username, password, session)
    except:
        return await new_login_openlaw(username, password, session)

    
    

