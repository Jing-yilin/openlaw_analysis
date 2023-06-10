import requests, re, time, tqdm, json
import pandas as pd
import yaml
from utils.file_control import create_dir

class OpenLawSpider:
    def __init__(self, keyword, strat_page, end_page, cookie, user_agent, links=[], contents = []):
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
        url = f"http://openlaw.cn/search/judgement/advanced?showResults=true&keyword={keyword_}&causeId=&caseNo=&litigationType=&docType=&litigant=&plaintiff=&defendant=&thirdParty=&lawyerId=&lawFirmId=&legals=&courtId=&judgeId=&clerk=&judgeDateYear=&judgeDateBegin=&judgeDateEnd=&zone=&procedureType=&lawId=&lawSearch=&courtLevel=&judgeResult=&wordCount=&page={page}"
        text = requests.get(url, headers=self.headers).text
        # 把keyword中文转换成url编码
        # 1. 创建正则表达式对象
        pattern = re.compile(r"/judgement/[0-9a-z]*\?keyword=" + keyword_)
        # 2. 使用正则表达式对象匹配text
        link_result = pattern.findall(text)
        return link_result

    def crawl_links(self) -> bool:
        print(f"======开始爬取链接======")
        links = []
        pages = list(range(self.strat_page, self.end_page + 1))
        for page in tqdm.tqdm(pages):
            link_result = self.get_url(page)
            links.extend(link_result)
            # 睡眠5秒
            time.sleep(2)
        print(f"======链接爬取完成======")
        links = ["http://openlaw.cn" + link for link in links]
        self.links = links
        if links is None or len(links) == 0:
            print(f"没有爬取到链接,请更新cookie!!!")
            return False
        else:
            file_name = f"{self.save_dir}/{self.keyword}_links.csv"
            with open(
                file_name, "w", encoding="utf-8"
            ) as f:
                for link in links:
                    f.write(link + "\n")
            print(f"======{file_name}保存完成======")
            return True

    def filter_text(self, text)->str:
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
        for url in tqdm.tqdm(self.links):
            print(f"正在爬取内容:{url}")
            content = self.get_content(url)
            contents.append(content)
            time.sleep(2)
        print(f"======内容爬取完成======")
        self.contents = contents
        file_name = f"{self.save_dir}/{self.keyword}_contents.json"
        # 保存
        with open(
            file_name, "w", encoding="utf-8"
        ) as f:
            json.dump(contents, f, ensure_ascii=False)
        print(f"======{file_name}保存完成======")

    def save_to_excel(self):
        df = pd.DataFrame(self.contents)
        # 修改标题
        df.rename(
            columns={
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




