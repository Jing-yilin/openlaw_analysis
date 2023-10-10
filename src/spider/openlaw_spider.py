import requests
import re
import json
import pandas as pd
import asyncio
import aiohttp
import os
import sys
import pathlib

from ..utils import create_dir


DOC_TYPE_MAP = {
    "": "",
    "通知书": "Notification",
    "判决书": "Verdict",
    "调解书": "Mediation",
    "决定书": "Decision",
    "令": "Warrant",
    "裁定书": "Ruling",
    "其他": "Other",
}

PROCEDURE_TYPE_MAP = {
    "": "",
    "一审": "First",
    "二审": "Second",
    "再审": "Retrial",
    "复核": "Review",
    "刑罚变更": "PenaltyChange",
    "其他": "Other",
}

COURT_LEVEL_MAP = {
    "": "",
    "最高人民法院": "0",
    "高级人民法院": "1",
    "中级人民法院": "2",
    "基层人民法院": "3",
}


JUDGE_RESULT_MAP = {
    "": "",
    "未知": "Unknow",
    "完全支持": "Victory",
    "部分支持": "Half",
    "不支持": "Half",
    "撤销": "Half",
    "其他": "Other",
}


LITIGATION_TYPE_MAP = {
    "": "",
    "民事": "Civil",
    "刑事": "Criminal",
    "行政": "Administration",
    "赔偿": "Compensation",
    "执行": "Execution",
}

ZONE_MAP = {
    "":"",
    "北京市": "北京市",
    "天津市": "天津市",
    "河北省": "河北省",
    "山西省": "山西省",
    "内蒙古自治区": "内蒙古自治区",
    "辽宁省": "辽宁省",
    "吉林省": "吉林省",
    "黑龙江省": "黑龙江省",
    "上海市": "上海市",
    "江苏省": "江苏省",
    "浙江省": "浙江省",
    "安徽省": "安徽省",
    "福建省": "福建省",
    "江西省": "江西省",
    "山东省": "山东省",
    "河南省": "河南省",
    "湖北省": "湖北省",
    "湖南省": "湖南省",
    "广东省": "广东省",
    "广西壮族自治区": "广西壮族自治区",
    "海南省": "海南省",
    "重庆市": "重庆市",
    "四川省": "四川省",
    "贵州省": "贵州省",
    "云南省": "云南省",
    "西藏自治区": "西藏自治区",
    "陕西省": "陕西省",
    "甘肃省": "甘肃省",
    "青海省": "青海省",
    "宁夏回族自治区": "宁夏回族自治区",
    "新疆维吾尔自治区": "新疆维吾尔自治区",
    "台湾省": "台湾省",
    "香港特别行政区": "香港特别行政区",
    "澳门特别行政区": "澳门特别行政区",
}

class OpenLawSpider:
    def __init__(
        self,
        config: dict,
        links: dict = {},
        contents: list = [],
        session: aiohttp.ClientSession = None,
        concurrent: int = 10,
    ):
        self.base_url = "http://openlaw.cn"

        self.config = config
        self.cookie = config["cookie"]
        self.user_agent = config["user_agent"]
        self.keyword = config["关键词"]
        self.litigation_type = LITIGATION_TYPE_MAP[config["案件类型"]]
        self.doc_type = DOC_TYPE_MAP[config["文书类型"]]
        self.zone = config["法院（地区）"]
        self.procedure_type = PROCEDURE_TYPE_MAP[config["审判程序"]]
        self.court_level = COURT_LEVEL_MAP[config["法院层级"]]
        self.judge_result = JUDGE_RESULT_MAP[config["判决结果"]]
        self.judge_date_begin = config["判决开始时间"]
        self.judge_date_end = config["判决结束时间"]
        self.strat_page = config["strat_page"]
        self.end_page = config["end_page"]

        self.headers = {
            "User-Agent": self.user_agent,
            "Cookie": self.cookie,
        }
        self.links = links
        self.contents = contents
        self.session = session
        self.concurrent = concurrent
        self.base_dir = f'./data/{config["关键词"]}_{config["案件类型"]}_{config["文书类型"]}_{config["法院（地区）"]}_{config["审判程序"]}_{config["法院层级"]}_{config["判决结果"]}_{config["判决开始时间"]}_{config["判决结束时间"]}'
        create_dir(self.base_dir)

    async def get_url(
        self, target_page_queue: asyncio.Queue, session: aiohttp.ClientSession
    ) -> list:
        while not target_page_queue.empty():
            page = await target_page_queue.get()
            keyword_ = requests.utils.quote(self.keyword)
            url = f"{self.base_url}/search/judgement/advanced?showResults=true&keyword={keyword_}&causeId=&caseNo=&litigationType={self.litigation_type}&docType={self.doc_type}&litigant=&plaintiff=&defendant=&thirdParty=&lawyerId=&lawFirmId=&legals=&courtId=&judgeId=&clerk=&judgeDateYear=&judgeDateBegin={self.judge_date_begin}&judgeDateEnd={self.judge_date_end}&zone={self.zone}&procedureType={self.procedure_type}&lawId=&lawSearch=&courtLevel={self.court_level}&judgeResult={self.judge_result}&wordCount=&page={page}"
            print(f"\n- 正在爬取第{page}页: {url}")
            async with session.get(url, headers=self.headers) as response:
                text = await response.text()
            # 把keyword中文转换成url编码
            # 1. 创建正则表达式对象
            pattern = re.compile(r"/judgement/[0-9a-z]*\?keyword=" + keyword_)
            # 2. 使用正则表达式对象匹配text
            link_result = pattern.findall(text)
            link_result = [self.base_url + link for link in link_result]
            if link_result:
                self.links[page] = link_result

    async def crawl_links(self) -> bool:
        # 错误处理
        if self.strat_page > self.end_page:
            print(f"起始页{self.strat_page}大于结束页{self.end_page}!!!")
            return False
        links = {}
        file_name = self.base_dir + "/links.json"
        str_pages = list(
            str(i) for i in range(self.strat_page, self.end_page + 1)
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

        target_page_queue = asyncio.Queue()
        for page in target_pages:
            await target_page_queue.put(page)

        print(f"======开始爬取链接======")

        tasks = []
        for i in range(self.concurrent):
            tasks.append(self.get_url(target_page_queue, self.session))
        await asyncio.gather(*tasks)
        print(f"======链接爬取完结束=====")

        if self.links is None or len(self.links.keys()) == 0:
            print(f"没有爬取到链接,请更新cookie!!!")
            return False
        else:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(self.links, f, ensure_ascii=False)
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

    async def add_content(
        self, url_queue: asyncio.Queue, session: aiohttp.ClientSession
    ) -> None:
        while not url_queue.empty():
            content = {}
            url = await url_queue.get()
            print(f"\n- 正在爬取: {url}")
            async with session.get(url, headers=self.headers) as response:
                text = await response.text()
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
            self.contents.append(content)


    async def crawl_contents(self):
        contents = []
        urls = []  # 已经爬取过的链接
        file_name = self.base_dir + "/contents.json"
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

        # 创建队列
        url_queue = asyncio.Queue()
        for url in target_urls:
            if url not in urls:
                await url_queue.put(url)

        print(f"======开始创建爬取任务======")
        tasks = []
        for i in range(self.concurrent):
            tasks.append(self.add_content(url_queue, self.session))

        await asyncio.gather(*tasks)

        print(f"======内容爬取完成======")
        # 保存
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(self.contents, f, ensure_ascii=False)
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
        file_name = self.base_dir + "/contents.xlsx"

        df.to_excel(file_name, index=False)
        print(f"======{file_name}保存完成======")
