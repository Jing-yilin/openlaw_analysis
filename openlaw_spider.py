import requests, re, time, tqdm, json
import pandas as pd
import yaml
import os
from utils.file_control import create_dir


class OpenLawSpider:
    def __init__(
        self, keyword, strat_page, end_page, cookie, user_agent, links={}, contents=[]
    ):
        self.base_url = "http://openlaw.cn"
        self.keyword = keyword
        self.strat_page = strat_page
        self.end_page = end_page
        self.save_dir = f"./data/{keyword}"
        self.cookie = cookie
        self.user_agent = user_agent
        self.headers = {
            "User-Agent": user_agent,
            "Cookie": cookie,
        }
        self.links = links
        self.contents = contents
        create_dir(self.save_dir)

    def get_url(self, page: str) -> list:
        keyword_ = requests.utils.quote(self.keyword)
        url = f"{self.base_url}/search/judgement/advanced?showResults=true&keyword={keyword_}&causeId=&caseNo=&litigationType=&docType=&litigant=&plaintiff=&defendant=&thirdParty=&lawyerId=&lawFirmId=&legals=&courtId=&judgeId=&clerk=&judgeDateYear=&judgeDateBegin=&judgeDateEnd=&zone=&procedureType=&lawId=&lawSearch=&courtLevel=&judgeResult=&wordCount=&page={page}"
        text = requests.get(url, headers=self.headers).text
        # 把keyword中文转换成url编码
        # 1. 创建正则表达式对象
        pattern = re.compile(r"/judgement/[0-9a-z]*\?keyword=" + keyword_)
        # 2. 使用正则表达式对象匹配text
        link_result = pattern.findall(text)
        link_result = [self.base_url + link for link in link_result]
        return link_result

    def crawl_links(self) -> bool:
        links = {}
        file_name = f"{self.save_dir}/{self.keyword}_links.json"
        target_pages = list(range(self.strat_page, self.end_page + 1))
        # 情况1： 链接已经爬取过了
        if os.path.exists(file_name):
            links = json.load(open(file_name, "r", encoding="utf-8"))
            self.links = links
            # 从self.links中删除不在target_pages中的page
            for page in self.links.keys():
                if page not in target_pages:
                    self.links.pop(page)
            for page in range(self.strat_page, self.end_page + 1):
                if page in self.links.keys():
                    target_pages.remove(page)

        print(f"======开始爬取链接======")
        for page in tqdm.tqdm(target_pages):
            link_result = self.get_url(page)
            if link_result is None or len(link_result) == 0:
                print(f"第{page}页没有爬取到链接!!!")
                continue
            # 同时记录page和link_result
            self.links[page] = link_result
            links[page] = link_result
            # 睡眠5秒
            time.sleep(2)
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
        if text is None or len(text) == 0:
            return ""
        else:
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

    def get_content(self, url: str) -> dict:
        content = {}
        text = requests.get(url, headers=self.headers).text
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
        contents = []
        urls = []  # 已经爬取过的链接
        file_name = f"{self.save_dir}/{self.keyword}_contents.json"
        target_urls = []
        for page, links in self.links.items():
            target_urls.extend(links)

        # 打开文件检查是否已经爬取过
        if os.path.exists(file_name):
            contents = json.load(open(file_name, "r", encoding="utf-8"))
            self.contents = contents
            # 已经爬取过的链接
            urls = [content["url"] for content in self.contents]
            # 去除已爬取过的内容了 链接不属于self.links的内容
            for row in self.contents:
                if row["url"] not in target_urls:
                    self.contents.remove(row)

        for link in tqdm.tqdm(target_urls):
            if link in urls:
                print(f"链接:{link} 已经爬取过")
                continue
            print(f"正在爬取内容:{link}")
            content = self.get_content(link)
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
