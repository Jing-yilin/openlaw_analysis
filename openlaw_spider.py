import requests
import re
import time
import tqdm
import json
import pandas as pd
import os
import sys
import time
from utils.file_control import create_dir
from utils.encryption import key_encrypt


class OpenLawSpider:
    """
    @description: OpenLawSpider类,用于爬取openlaw.cn的数据,记录链接和内容
    @param {str} username: 用户名
    @param {str} password: 密码
    @param {str} keyword: 关键词
    @param {int} start_page: 起始页
    @param {int} end_page: 结束页
    @param {str} cookie: cookie
    @param {str} user_agent: user_agent
    """

    def __init__(
        self,
        username,
        password,
        keyword,
        start_page,
        end_page,
        cookie,
        user_agent,
    ):
        self.base_url = "http://openlaw.cn"
        self.set_username(username)
        self.set_password(password)
        self.set_keyword(keyword)
        self.set_page(start_page, end_page)
        self.set_save_dir(f"./data/{keyword}")
        self.set_cookie(cookie)
        self.set_user_agent(user_agent)
        self.set_headers(user_agent, cookie)
        self.set_timestamp(time.time())
        self.links = {}
        self.contents = []
        self.update_cookie()
        create_dir(self.save_dir)
    
    def update_cookie(self):
        url = self.base_url + "/login.jsp"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        if response.status_code != 200:
            print("更新cookie失败!!!")
            return
        if response.headers["Set-Cookie"]:
            text = response.text
            pattern = re.compile(r'<input type="hidden" name="_csrf" value="(.*)"/>')
            csrf = pattern.findall(text)[0]
            session = response.headers["Set-Cookie"]
            last_timestamp = self.timestamp
            timestamp = int(time.time())
            self.set_timestamp(timestamp)
            #  "Hm_lvt_a105f5952beb915ade56722dc85adf05=1686368033; SESSION=NTYwNTUxZTQtZmE4Ni00Y2FlLWJkYWUtNjE1NGU1NGEzYjQ3; Hm_lpvt_a105f5952beb915ade56722dc85adf05=1686453940"
            cookie = f"Hm_lvt_a105f5952beb915ade56722dc85adf05={self.timestamp}; SESSION={session}; Hm_lpvt_a105f5952beb915ade56722dc85adf05={last_timestamp}"
            self.set_cookie(cookie)
            self.set_headers(self.user_agent, self.cookie)
            print("cookie更新成功!!!")
        else:
            print("cookie没有更新!!!")

        url = self.base_url + "/login" # http://openlaw.cn/login
        print("url: ", url)
        data = {
            "_csrf": csrf,
            "username": requests.utils.quote(self.username),
            "password": key_encrypt(self.password),
            "_spring_security_remember_me": "true",
        }
        '''
            POST /login HTTP/1.1
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
            Accept-Encoding: gzip, deflate
            Accept-Language: en,zh-CN;q=0.9,zh;q=0.8
            Cache-Control: no-cache
            Content-Length: 518
            Content-Type: application/x-www-form-urlencoded
            Cookie: SESSION=MDYwODViMTctZGQwZC00NTgyLWFmYTYtZmIyY2Y5NTU0NjYx; Hm_lvt_a105f5952beb915ade56722dc85adf05=1686975569,1687153114,1687258170,1687258428; Hm_lpvt_a105f5952beb915ade56722dc85adf05=1687277334
            Host: openlaw.cn
            Origin: http://openlaw.cn
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Referer: http://openlaw.cn/login.jsp
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36
            sec-gpc: 1
        '''
        headers = {
            "Host": "openlaw.cn",
            "User-Agent": self.user_agent,
            "Cookie": self.cookie,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://openlaw.cn",
            "Connection": "keep-alive",
            "Referer": "http://openlaw.cn/login.jsp",
            "Upgrade-Insecure-Requests": "1",
            "Sec-GPC": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

        print(f"data: {data}")
        response = requests.post(url, data=data, headers=headers, timeout=10)
        print(response.status_code)
        print(response.headers)
        # 保存 response.text
        with open("./response.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        # url = self.base_url + "/login.jsp?$=success"
        # print("url: ", url)
        # headers = {
        #     "Host": "openlaw.cn",
        #     "User-Agent": self.user_agent,
        #     "Cookie": self.cookie,
        #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        #     "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        #     "Accept-Encoding": "gzip, deflate",
        #     "Connection": "keep-alive",
        #     "Referer": "http://openlaw.cn/login.jsp",
        #     "Upgrade-Insecure-Requests": "1",
        #     "Sec-GPC": "1",
        # }
        # response = requests.get(url, headers=headers, timeout=10)
        # print(response.status_code)
        # print(response.headers)
        # print(response.text)
        sys.exit()



    def find_url(self, page: str) -> list:
        """
        @description: 获取链接
        @param {str} page: 页码
        @return {list} link_result: 链接列表
        """
        keyword_ = requests.utils.quote(self.keyword)
        url = f"{self.base_url}/search/judgement/advanced?showResults=true&keyword={keyword_}&causeId=&caseNo=&litigationType=&docType=&litigant=&plaintiff=&defendant=&thirdParty=&lawyerId=&lawFirmId=&legals=&courtId=&judgeId=&clerk=&judgeDateYear=&judgeDateBegin=&judgeDateEnd=&zone=&procedureType=&lawId=&lawSearch=&courtLevel=&judgeResult=&wordCount=&page={page}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            text = response.text
        except requests.Timeout:
            print(f"请求{url}超时!!!")
            return None
        except Exception as e:
            print(f"请求{url}失败!!!")
            print(e)
            return None
        # 把keyword中文转换成url编码
        # 1. 创建正则表达式对象
        pattern = re.compile(r"/judgement/[0-9a-z]*\?keyword=" + keyword_)
        # 2. 使用正则表达式对象匹配text
        link_result = pattern.findall(text)
        link_result = [self.base_url + link for link in link_result]
        return link_result

    def crawl_links(self) -> bool:
        """
        @description: 爬取链接
        @return {bool} True: 爬取成功; False: 爬取失败
        """
        links = {}
        file_name = f"{self.save_dir}/{self.keyword}_links.json"
        str_pages = list(
            str(i) for i in range(self.start_page, self.end_page + 1)
        )  # ["1", "2", "3", "4", "5", ...]
        target_pages = str_pages.copy()  # ["1", "2", "3", "4", "5", ...]
        # 情况: 链接已经爬取过了
        if os.path.exists(file_name):
            print(f"======{file_name}已经存在，正在查看======")
            links = json.load(open(file_name, "r", encoding="utf-8"))  # 读取在本地的links
            self.links = links
            # 从self.links中删除不在target_pages中的page
            pages = list(self.links.keys())
            for page in pages:
                if page not in target_pages:
                    self.links.pop(page)
            for page in str_pages:
                if page in pages:
                    target_pages.remove(page)
        if len(target_pages) == 0:
            print(f"======所有链接已经爬取过了======")
            return True

        print(f"======开始爬取链接======")
        for page in tqdm.tqdm(target_pages):
            link_result = self.find_url(page)
            if link_result is None or len(link_result) == 0:
                print(f"第{page}页没有爬取到链接!!!")
                continue
            else:
                # 同时记录page和link_result
                self.links[page] = link_result
                links[page] = link_result
                # 睡眠5秒
                time.sleep(2)
                print("睡眠2秒")
        print(f"======链接爬取完结束=====")

        if self.links is None or len(self.links.keys()) == 0:
            print(f"没有爬取到链接,请更新cookie!!!")
            return False
        else:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(links, f, ensure_ascii=False)
            print(f"======{file_name}保存完成======")
            return True

    def filter_text(self, text) -> str:
        """
        @description: 过滤文本
        @param {str} text: 文本
        @return {str} text: 过滤后的文本
        """
        if text is None or len(text) == 0:
            return ""
        text = text[0]
        text = text.strip()
        # 去除text中的所有<a><\a>的内容
        text = re.sub(r"<a.*?>|<\/a>", "", text)
        # 去除text中的所有<em><\em>的内容
        text = re.sub(r"<em.*?>|<\/em>", "", text)
        # 去除text中的所有<span><\span>的内容
        text = re.sub(r"<span.*?>|<\/span>", "", text)
        # 去除text中的所有<p><\p>的内容
        text = re.sub(r"<p.*?>|<\/p>", "", text)
        # 去除 &nbsp; &lt; &gt; &amp;
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&nbsp;", "", text)
        return text

    def find_content(self, url: str) -> dict:
        """
        @description: 获取文书原始内容
        @param {str} url: 文书链接
        @return {dict} content: 文书内容
        """
        content = {}
        try:
            response = requests.get(url, headers=self.headers, timeout=10)  # Set the timeout value (in seconds)
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            text = response.text
        except requests.Timeout:
            print(f"请求{url}超时!!!")
            return None
        except requests.RequestException as e:
            print(f"请求{url}失败!!!")
            return None
        
        content["url"] = url
        content["title"] = self.filter_text(
            re.findall('<h2 class="entry-title">(.*)</h2>', text)
        )
        content["case_number"] = self.filter_text(
            re.findall('<li class="clearfix ht-kb-pf-standard">案号：(.*)</li>', text)
        )
        content["court"] = self.filter_text(
            re.findall('<li class="clearfix ht-kb-pf-standard">法院：(.*)</li>', text)
        )
        content["data"] = self.filter_text(
            re.findall('<li class="clearfix ht-kb-pf-standard">时间：(.*)</li>', text)
        )
        content["cause"] = self.filter_text(
            re.findall('<li class="clearfix ht-kb-pf-standard">案由：(.*)</li>', text)
        )
        content["type"] = self.filter_text(
            re.findall('<li class="clearfix ht-kb-pf-standard">类型：(.*)</li>', text)
        )
        content["procedure"] = self.filter_text(
            re.findall('<li class="clearfix ht-kb-pf-standard">程序：(.*)</li>', text)
        )
        content["procedure_explain"] = self.filter_text(
            re.findall(
                '<div class="part" id="Explain">\s*<!--.*?-->\s*<p>(.*?)<\/p>\s*<\/div>',
                text,
            )
        )
        content["tags"] = (
            re.findall('<a href="[^"]+" rel="tag">(.*?)</a>', text)
            if re.findall('<a href="[^"]+" rel="tag">(.*?)</a>', text)
            else ""
        )
        content["opinion"] = self.filter_text(
            re.findall(
                '<div class="part" id="Opinion">\s*<!--.*?-->\s*<p>(.*?)<\/p>\s*<\/div>',
                text,
            )
        )
        content["verdict"] = self.filter_text(
            re.findall(
                '<div class="part" id="Verdict">\s*<!--.*?-->\s*<p>(.*?)<\/p>\s*<\/div>',
                text,
            )
        )
        return content

    def crawl_contents(self):
        """
        @description: 爬取文书内容
        @return: None
        """
        contents = []
        urls = []  # 已经爬取过的链接
        file_name = f"{self.save_dir}/{self.keyword}_contents.json"
        tarfind_urls = []
        for page, links in self.links.items():
            tarfind_urls.extend(links)

        # 打开文件检查是否已经爬取过
        if os.path.exists(file_name):
            contents = json.load(open(file_name, "r", encoding="utf-8"))
            self.contents = contents
            # 已经爬取过的链接
            urls = [content["url"] for content in self.contents]
            # 去除已爬取过的内容了 链接不属于self.links的内容
            for row in self.contents:
                if row["url"] not in tarfind_urls:
                    self.contents.remove(row)

        for link in tqdm.tqdm(tarfind_urls):
            if link in urls:
                print(f"链接:{link} 已经爬取过")
                continue
            print(f"正在爬取内容:{link}")
            content = self.find_content(link)
            self.contents.append(content)
            contents.append(content)
            time.sleep(2)
        print(f"======内容爬取完成======")
        # 保存
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(contents, f, ensure_ascii=False)
        print(f"======{file_name}保存完成======")

    def save_to_excel(self):
        df = pd.DataFrame(self.contents)
        # 修改标题
        df.rename(
            columns={
                "url": "链接",
                "title": "标题",
                "case_number": "案号",
                "court": "法院",
                "data": "日期",
                "cause": "案由",
                "type": "类型",
                "procedure": "程序",
                "procedure_explain": "程序说明",
                "tags": "标签",
                "opinion": "观点",
                "verdict": "判决",
            },
            inplace=True,
        )
        # 保存到excel
        file_name = f"{self.save_dir}/{self.keyword}_contents.xlsx"
        df.to_excel(file_name, index=False)
        print(f"======{file_name}保存完成======")

    def set_username(self, username):
        """
        @description: 设置用户名
        @param {type} username: 用户名
        @return: None
        """
        self.username = username

    def set_password(self, password):
        """
        @description: 设置密码
        @param {type} password: 密码
        @return: None
        """
        self.password = password

    def set_keyword(self, keyword):
        """
        @description: 设置关键词
        @param {type} keyword: 关键词
        @return: None
        """
        self.keyword = keyword

    def set_save_dir(self, save_dir):
        """
        @description: 设置保存目录
        @param {type} save_dir: 保存目录
        @return: None
        """
        self.save_dir = save_dir
    
    def set_page(self, start_page, end_page):
        """
        @description: 设置爬取页码
        @param {type} start_page: 开始页码
        @param {type} end_page: 结束页码
        @return: None
        """
        assert start_page <= end_page, "开始页码必须小于等于结束页码"
        self.start_page = start_page
        self.end_page = end_page

    def set_cookie(self, cookie):
        """
        @description: 设置cookie
        @param {type} cookie: cookie
        @return: None
        """
        self.cookie = cookie

    def set_user_agent(self, user_agent):
        """
        @description: 设置user_agent
        @param {type} user_agent: user_agent
        @return: None
        """
        self.user_agent = user_agent

    def set_headers(self,uer_agent, cookie):
        """
        @description: 设置headers
        @param {type} headers: headers
        @return: None
        """
        self.headers = {
            "Host": "openlaw.cn",
            "User-Agent": uer_agent,
        }

    def set_timestamp(self, timestamp):
        """
        @description: 设置时间戳
        @param {type} timestamp: 时间戳
        @return: None
        """
        self.timestamp = timestamp

    

