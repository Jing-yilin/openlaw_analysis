import aiohttp
import asyncio
import re
import pathlib
import sys
import yaml
import os
import requests
from logging import Logger

sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))

from utils import encrypt_js, create_dir


def check_login_status(
    username: str,
    password: str,
    logger: Logger = None,
):
    """
    如果保存的cookie_session有效，则返回cookie_session
    否则返回False
    """
    logger.info(f"======正在检查用户 {username} 的登录状态======")
    if not username or not password:
        logger.info("用户名或密码为空")
        return False

    all_user_data_path = (
        str(pathlib.Path(__file__).parent.parent.parent.absolute())
        + "/data/all_user_data"
    )
    user_data_file = all_user_data_path + "/" + username + ".yaml"

    if not os.path.exists(user_data_file):
        logger.error("用户文件不存在")
        return False

    try:
        # 读取旧的session
        with open(user_data_file, "r") as f:
            user_data = yaml.load(f, Loader=yaml.FullLoader)
            cookie_session = user_data["cookie_session"]
            logger.info(f"读取到旧的cookie_session: {cookie_session}")

        # 尝试使用旧的session登录
        url = "http://openlaw.cn/login.jsp"
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
            "Cache-Control": "no-cache",
        }

        logger.info(f"开始提交get请求至 {url}")
        try:
            resp = requests.get(url, headers=headers)
            if not resp.status_code == 200:
                logger.error(f"[{resp.status_code} ERROR] 无法访问: {url}")
                return False
            # 如果resp里面没有set-cookie字段，说明session有效
            if not resp.headers.get("set-cookie"):
                logger.info("旧的session登录成功")
                return cookie_session
            else:
                logger.info("旧的session登录失败")
                return False
        except Exception as e:
            logger.error("旧的session登录失败,原因是: " + str(e))
            return False

    except Exception as e:
        logger.error("旧的session登录失败,原因是: " + str(e))
        return False


async def new_login_openlaw(
    username: str, password: str, session: aiohttp.ClientSession, logger: Logger = None
) -> str:
    all_user_data_path = (
        str(pathlib.Path(__file__).parent.parent.parent.absolute())
        + "/data/all_user_data"
    )
    user_data_file = all_user_data_path + "/" + username + ".yaml"
    create_dir(all_user_data_path)

    try:
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
            "Cache-Control": "no-cache",
        }
        logger.info(f"开始提交get请求至 {url}")
        async with session.get(url, headers=headers) as resp:
            if not resp.status == 200:
                logger.error(f"[{resp.status} ERROR] 无法访问: {url}")
                return
            logger.info(f"[200 OK] 成功访问: {url}")
            text = await resp.text()
            csrf = re.findall(
                r'<input type="hidden" name="_csrf" value="(.*)"/>', text
            )[0]
            cookie_session = resp.cookies.get("SESSION").value
            logger.info(f"SESSION = {cookie_session}")
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
            "Sec-GPC": "1",
        }
        data = {
            "_csrf": csrf,
            "username": username,
            "password": encrypted_password,
            "_spring_security_remember_me": "true",
        }
        logger.info(f"开始提交post请求至 {url}")
        async with session.post(url, headers=headers, data=data) as resp:
            if not resp.status == 200:
                logger.error(f"[{resp.status} ERROR] 无法访问: {url}")
                return
            logger.info(f"[200 OK] 成功访问: {url}")

        # 保存session到用户文件
        with open(user_data_file, "w") as f:
            yaml.dump({
                "cookie_session": cookie_session,
                "username": username,
                "password": password
                }, f)

        return "SESSION=" + cookie_session

    except Exception as e:
        logger.error("登录失败,原因是: " + str(e))
        return None


async def login_openlaw(
    username: str, password: str, session: aiohttp.ClientSession, logger:Logger=None
) -> str:
    """
    如果登陆成功: cookie
    如果登陆失败: 返回None
    """

    cookie_session = check_login_status(username, password, logger)
    if cookie_session:
        logger.info("登录状态检查成功，无需重新登录")
        return "SESSION=" + cookie_session
    else:
        logger.info("登录状态检查失败，开始重新登录")
        return await new_login_openlaw(username, password, session, logger=logger)
