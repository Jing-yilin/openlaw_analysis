import requests
import re
import json
import pandas as pd
import asyncio
import aiohttp
import os
from bs4 import BeautifulSoup
import sys
import pathlib
from tqdm import tqdm
import warnings
from tqdm.asyncio import tqdm_asyncio
from logging import Logger

warnings.filterwarnings("ignore")

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from ..utils import create_dir
from ..chat_model import get_conversation_chain, LAW_RESULT_TEMPLATE


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
    "": "",
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
        concurrent: int = 50,
        ai_mode=True,
        logger: Logger = None,
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
        self.num = config["数量"]
        self.start_page = 1
        self.end_page = (self.num - 1) // 10 + 1

        self.headers = {
            "User-Agent": self.user_agent,
            "Cookie": self.cookie,
        }
        self.links = links
        self.contents = contents
        self.session = session
        self.concurrent = concurrent
        self.__base_dir = f'./data/{config["关键词"]}_{config["案件类型"]}_{config["文书类型"]}_{config["法院（地区）"]}_{config["审判程序"]}_{config["法院层级"]}_{config["判决结果"]}_{config["判决开始时间"]}_{config["判决结束时间"]}'
        create_dir(self.__base_dir)
        self.logger = logger

    async def get_url(
        self, target_page_queue: asyncio.Queue, session: aiohttp.ClientSession
    ) -> list:
        while not target_page_queue.empty():
            try:
                page = await target_page_queue.get()
                keyword_ = requests.utils.quote(self.keyword)
                url = f"{self.base_url}/search/judgement/advanced?showResults=true&keyword={keyword_}&causeId=&caseNo=&litigationType={self.litigation_type}&docType={self.doc_type}&litigant=&plaintiff=&defendant=&thirdParty=&lawyerId=&lawFirmId=&legals=&courtId=&judgeId=&clerk=&judgeDateYear=&judgeDateBegin={self.judge_date_begin}&judgeDateEnd={self.judge_date_end}&zone={self.zone}&procedureType={self.procedure_type}&lawId=&lawSearch=&courtLevel={self.court_level}&judgeResult={self.judge_result}&wordCount=&page={page}"
                self.logger.info(f"正在爬取第{page}页: {url}")
                async with session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    text = await response.text()
                    self.logger.info(f"====== 爬取成功, 状态码: {response.status} ======")
            except Exception as e:
                self.logger.error(f"爬取失败: {url}\n"
                      f"错误信息: {e}")
                await target_page_queue.put(page)
                raise e
            # 把keyword中文转换成url编码
            # 1. 创建正则表达式对象
            pattern = re.compile(r"/judgement/[0-9a-z]*\?keyword=" + keyword_)
            # 2. 使用正则表达式对象匹配text
            link_result = pattern.findall(text)
            link_result = [self.base_url + link for link in link_result]
            if link_result:
                self.links[page] = link_result

            await asyncio.sleep(0.15)

    async def crawl_links(self) -> bool:
        # 错误处理
        if self.start_page > self.end_page:
            self.logger.error(f"起始页{self.start_page}大于结束页{self.end_page}!!!")
            return False
        links = {}
        file_name = self.__base_dir + "/links.json"
        str_pages = list(
            str(i) for i in range(self.start_page, self.end_page + 1)
        )  # ["1", "2", "3", "4", "5", ...]
        target_pages = str_pages.copy()  # ["1", "2", "3", "4", "5", ...]
        # 情况: 链接已经爬取过了
        if os.path.exists(file_name):
            self.logger.info(f"======{file_name}已经存在，正在查看======")
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
            self.logger.info(f"======所有链接已经爬取过了======")
            return True

        target_page_queue = asyncio.Queue()
        for page in target_pages:
            await target_page_queue.put(page)

        self.logger.info(f"======开始爬取链接======")

        tasks = []
        temp_concurrent = self.concurrent
        while (not target_page_queue.empty()) and (temp_concurrent > 0):
            try:
                for i in range(temp_concurrent):
                    tasks.append(self.get_url(target_page_queue, self.session))
                await asyncio.gather(*tasks)
            # [Errno 54] Connection reset by peer
            except Exception as e:
                self.logger.error(e)
                self.logger.info(f"并发数量超过最大值太多, 减少并发数量[{temp_concurrent} -> {temp_concurrent//2}]")
                temp_concurrent = temp_concurrent // 2

            asyncio.sleep(0.1)

        self.logger.info(f"======链接爬取完结束=====")

        if self.links is None or len(self.links.keys()) == 0:
            self.logger.error(f"没有爬取到任何符合条件的链接，请更改搜索条件！")
            return False
        else:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(self.links, f, ensure_ascii=False)
            self.logger.info(f"======{file_name}保存完成======")
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
            try:
                content = {}
                url = await url_queue.get()
                self.logger.info(f"\n- 正在爬取: {url}")
                async with session.get(url, headers=self.headers) as response:
                    text = await response.text()
            except Exception as e:
                await url_queue.put(url)
                raise e
            if text is None or len(text) == 0:
                self.logger.error(f"爬取失败: {url}")
                continue
            soup = BeautifulSoup(text, "html.parser")
            content["链接"] = url
            try:
                content["标题"] = soup.find("h2", class_="entry-title").text.strip()  # 标题
            except Exception as e:
                content["标题"] = ""
                print(f"标题爬取失败: {url}")
                # print(e)
            try:
                content["日期"] = (
                    soup.find("li", class_="ht-kb-em-date")
                    .text.strip()
                    .split("日期：")[-1]
                )  # 日期
            except Exception as e:
                content["日期"] = ""
                # print(f"日期爬取失败: {url}")
                # print(e)
            try:
                content["法院"] = (
                    soup.find("li", class_="ht-kb-em-author")
                    .text.strip()
                    .split("法院：")[-1]
                )  # 法院
            except Exception as e:
                content["法院"] = ""
                # print(f"法院爬取失败: {url}")
                # print(e)
            try:
                content["案号"] = (
                    soup.find("li", class_="ht-kb-em-category")
                    .text.strip()
                    .split("案号：")[-1]
                )  # 案号
            except Exception as e:
                content["案号"] = ""
                # print(f"案号爬取失败: {url}")
                # print(e)
            try:
                litigants = soup.find("div", id="Litigants").wrap
                content["当事人"] = re.findall(r"<p>(.*?)</p>", str(litigants))  # 当事人
            except Exception as e:
                content["当事人"] = ""
                # print(f"当事人爬取失败: {url}")
                # print(e)
            try:
                content["庭审程序说明"] = soup.find(
                    "div", id="Explain"
                ).text.strip()  # 庭审程序说明
            except Exception as e:
                content["庭审程序说明"] = ""
                # print(f"庭审程序说明爬取失败: {url}")
                # print(e)

            try:
                content["庭审过程"] = soup.find("div", id="Procedure").text.strip()  # 庭审过程
            except Exception as e:
                content["庭审过程"] = ""
                # print(f"庭审过程爬取失败: {url}")
                # print(e)
            try:
                content["查明事实"] = soup.find("div", id="Facts").text.strip()  # 查明事实
            except Exception as e:  # 查明事实
                content["查明事实"] = ""
                # print(f"查明事实爬取失败: {url}")
                # print(e)
            try:
                content["法院意见"] = soup.find("div", id="Opinion").text.strip()  # 法院意见
            except Exception as e:
                content["法院意见"] = ""
                # print(f"法院意见爬取失败: {url}")
                # print(e)
            try:
                content["判决结果"] = soup.find("div", id="Verdict").text.strip()  # 判决结果
            except Exception as e:
                content["判决结果"] = ""
                # print(f"判决结果爬取失败: {url}")
                # print(e)
            try:
                content["庭后告知"] = soup.find("div", id="Inform").text.strip()  # 庭后告知
            except Exception as e:  # 庭后告知
                content["庭后告知"] = ""
                # print(f"庭后告知爬取失败: {url}")
                # print(e)
            try:
                content["结尾"] = soup.find("div", id="Ending").text.strip()  # 结尾
            except Exception as e:
                content["结尾"] = ""
                # print(f"结尾爬取失败: {url}")
                # print(e)

            try:
                info = (
                    soup.find(
                        "section", class_="widget HT_KB_Authors_Widget clearfix"
                    ).text.strip()
                    + "\n"
                )  # 案件信息
            except Exception as e:
                info = ""

            if info:
                try:
                    content["类型"] = (
                        re.findall(r"类型：(.*)\n", info)[0]
                        if self.doc_type == ""
                        else self.doc_type
                    )
                except Exception as e:
                    content["类型"] = ""
                try:
                    content["程序"] = (
                        re.findall(r"程序：(.*)\n", info)[0]
                        if self.procedure_type == ""
                        else self.procedure_type
                    )
                except Exception as e:
                    content["程序"] = ""
                try:
                    content["判决结果"] = re.findall(r"判决结果：(.*)\n", info)[0]
                except Exception as e:
                    content["判决结果"] = ""
                try:
                    content["涉诉机关类型"] = re.findall(r"涉诉机关类型：(.*)\n", info)[0]
                except Exception as e:
                    content["涉诉机关类型"] = ""
                try:
                    content["案由"] = re.findall(r"案由：(.*)\n", info)[0]
                except Exception as e:
                    content["案由"] = ""
            else:
                content["类型"] = ""
                content["程序"] = ""
                content["判决结果"] = ""
                content["涉诉机关类型"] = ""
                content["案由"] = ""
            try:
                content["标签"] = (
                    re.findall('<a href="[^"]+" rel="tag">(.*?)</a>', text)
                    if re.findall('<a href="[^"]+" rel="tag">(.*?)</a>', text)
                    else ""
                )
            except Exception as e:
                content["tags"] = ""
                # print(f"标签爬取失败: {url}")
                # print(e)

            self.contents.append(content)

    async def crawl_contents(self):
        contents = []
        urls = []  # 已经爬取过的链接
        file_name = self.__base_dir + "/contents.json"
        target_urls = []
        for page, links in self.links.items():
            if len(target_urls) >= self.num:
                break
            target_urls.extend(links)

        self.logger.info(f"======共有{len(target_urls)}条链接需要爬取======")

        
        # 打开文件检查是否已经爬取过
        if os.path.exists(file_name):
            contents = json.load(open(file_name, "r", encoding="utf-8"))
            self.contents = contents
            # 已经爬取过的链接
            urls = [content["链接"] for content in self.contents]
            # 去除已爬取过的内容了 链接不属于self.links的内容
            for row in self.contents:
                if row["链接"] not in target_urls:
                    self.contents.remove(row)
            # 去除已爬取过的链接
            for url in urls:
                if url in target_urls:
                    target_urls.remove(url)

        # 创建队列
        url_queue = asyncio.Queue()
        for url in target_urls:
            if url not in urls:
                await url_queue.put(url)

        self.logger.info(f"======开始创建爬取任务======")
        temp_concurrent = self.concurrent
        tasks = []
        while (not url_queue.empty()) and (temp_concurrent > 0):
            try:
                for i in range(temp_concurrent):
                    tasks.append(self.add_content(url_queue, self.session))
                await asyncio.gather(*tasks)
            except Exception as e:
                self.logger.error(e)
                self.logger.info(f"并发数量超过最大值太多, 减少并发数量[{temp_concurrent} -> {temp_concurrent//2}]")
                temp_concurrent = temp_concurrent // 2
            asyncio.sleep(0.1)

        self.logger.info(f"======内容爬取完成======")
        # 保存
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(self.contents, f, ensure_ascii=False)
        self.logger.info(f"======{file_name}保存完成======")

    def save_to_excel(self):
        df = pd.DataFrame(self.contents)
        # 保存到excel
        file_name = self.__base_dir + "/contents.xlsx"

        df.to_excel(file_name, index=False)
        self.logger.info(f"======{file_name}保存完成======")

    def basic_analysis(self):
        """
        分析：
        一审数量、二审数量、再审数量、复核数量、刑罚变更数量、其他数量
        裁定书数量、判决书数量、调解书数量、决定书数量、令数量、通知书数量、其他数量
        每个案由的数量
        每个标签的数量
        """
        if not self.contents:
            return {}
        analysis = {}
        # 一审数量、二审数量、再审数量、复核数量、刑罚变更数量、其他数量
        analysis["审判程序"] = {}

        for procedure_type in PROCEDURE_TYPE_MAP.keys():
            if procedure_type:
                analysis["审判程序"][procedure_type] = 0
        for content in self.contents:
            procedure_type = content["程序"]
            if procedure_type:
                if procedure_type in PROCEDURE_TYPE_MAP.keys():
                    analysis["审判程序"][procedure_type] += 1
                elif procedure_type in PROCEDURE_TYPE_MAP.values():
                    idx = list(PROCEDURE_TYPE_MAP.values()).index(procedure_type)
                    analysis["审判程序"][list(PROCEDURE_TYPE_MAP.keys())[idx]] += 1
                else:
                    continue
            else:
                continue
        # 裁定书数量、判决书数量、调解书数量、决定书数量、令数量、通知书数量、其他数量
        analysis["文书类型"] = {}
        for doc_type in DOC_TYPE_MAP.keys():
            if doc_type:
                analysis["文书类型"][doc_type] = 0
        for content in self.contents:
            doc_type = content["类型"]
            if doc_type:
                if doc_type in DOC_TYPE_MAP.keys():
                    analysis["文书类型"][doc_type] += 1
                elif doc_type in DOC_TYPE_MAP.values():
                    idx = list(DOC_TYPE_MAP.values()).index(doc_type)
                    analysis["文书类型"][list(DOC_TYPE_MAP.keys())[idx]] += 1
                else:
                    continue
            else:
                continue
        # 案由
        analysis["案由"] = {}
        for content in self.contents:
            case = content["案由"]
            if case:
                if case not in analysis["案由"]:
                    analysis["案由"][case] = 0
                analysis["案由"][case] += 1
        # 标签
        analysis["标签"] = {}
        for content in self.contents:
            tags = content["标签"]
            for tag in tags:
                if tag:
                    if tag not in analysis["标签"]:
                        analysis["标签"][tag] = 0
                    analysis["标签"][tag] += 1

        # 排序
        analysis["审判程序"] = dict(
            sorted(analysis["审判程序"].items(), key=lambda item: item[1], reverse=True)
        )
        analysis["文书类型"] = dict(
            sorted(analysis["文书类型"].items(), key=lambda item: item[1], reverse=True)
        )
        analysis["案由"] = dict(
            sorted(analysis["案由"].items(), key=lambda item: item[1], reverse=True)
        )
        analysis["标签"] = dict(
            sorted(analysis["标签"].items(), key=lambda item: item[1], reverse=True)
        )

        return analysis

    async def __ask_gpt(self, queue: asyncio.Queue):
        default_extraxtion_json = {
            "原告起诉的事实与理由": "",
            "原告起诉的法律依据": [],
            "原告起诉的诉讼请求": "",
            "被告辩称的事实与理由": "",
            "被告辩称的法律依据": [],
            "法院认定和查明的事实": "",
            "法院的判决的法律依据": [],
            "法院的判决结果": "",
        }
        while not queue.empty():
            content = await queue.get()
            self.logger.info(f"======目前正在处理 [{content['标题']}]======")
            if not content["庭审过程"]:
                content.update(default_extraxtion_json)
                self.logger.info(f"======✅{content['标题']} 没有庭审过程======")
                continue
            chain = get_conversation_chain(
                model_name="gpt-3.5-turbo-16k-0613", prompt=LAW_RESULT_TEMPLATE
            )
            try:
                extraxtion = chain.predict(
                    explain=content["庭审程序说明"],
                    procedure=content["庭审过程"],
                    facts=content["查明事实"],
                    opinion=content["法院意见"],
                )
                extraxtion_json = json.loads(extraxtion)
                content.update(extraxtion_json)
            except Exception as e:
                extraxtion_json = default_extraxtion_json
                self.logger.error(f"======❌{content['标题']} AI处理失败, 错误信息: {e}======"
                                  "默认使用空的结果")
            content.update(extraxtion_json)
            self.logger.info(f"======✅{content['标题']} AI处理完成======")

    async def ai_process(self):
        if not self.contents:
            return
        self.logger.info("======开始AI处理====")
        queue = asyncio.Queue()
        for content in self.contents:
            await queue.put(content)
        tasks = []
        temp_concurrent = self.concurrent // 2
        for i in range(temp_concurrent):
            tasks.append(self.__ask_gpt(queue))
        await asyncio.gather(*tasks)
        self.logger.info("======🤖✅AI处理完成======")

    @property
    def df(self):
        return pd.DataFrame(self.contents)

    @property
    def base_dir(self):
        return self.__base_dir

    @property
    def analysis(self):
        return self.basic_analysis()
