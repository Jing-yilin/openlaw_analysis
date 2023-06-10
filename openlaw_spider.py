import requests, bs4, re, os, time, tqdm, csv, json
import pandas as pd
import yaml

# 读取config.yaml文件

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    cookie = config["cookie"]
    user_agent = config["user_agent"]
    keyword = config["keyword"]
    strat_page = config["strat_page"]
    end_page = config["end_page"]

headers = {
    "User-Agent": user_agent,
    "Cookie": cookie,
}


def get_url(page: str, keyword: str):
    keyword = requests.utils.quote(keyword)
    url = f"http://openlaw.cn/search/judgement/advanced?showResults=true&keyword={keyword}&causeId=&caseNo=&litigationType=&docType=&litigant=&plaintiff=&defendant=&thirdParty=&lawyerId=&lawFirmId=&legals=&courtId=&judgeId=&clerk=&judgeDateYear=&judgeDateBegin=&judgeDateEnd=&zone=&procedureType=&lawId=&lawSearch=&courtLevel=&judgeResult=&wordCount=&page={page}"
    text = requests.get(url, headers=headers).text
    # 把keyword中文转换成url编码
    # 1. 创建正则表达式对象
    pattern = re.compile(r"/judgement/[0-9a-z]*\?keyword=" + keyword)
    # 2. 使用正则表达式对象匹配text
    link_result = pattern.findall(text)
    return link_result


def crawl_links(strat_page: int, end_page: int, keyword: str):
    print(f"======开始爬取链接======")
    links = []
    pages = list(range(strat_page, end_page + 1))

    for page in tqdm.tqdm(pages):
        link_result = get_url(page, keyword)
        links.extend(link_result)
        # 睡眠5秒
        time.sleep(2)
    print(f"======链接爬取完成======")

    if not os.path.exists("./data"):
        os.mkdir("./data")
    with open(f"./data/{keyword}_links.csv", "w", encoding="utf-8") as f:
        for link in links:
            link = "http://openlaw.cn" + link
            f.write(link + "\n")
    print(f"======保存完成======")

def filter_text(text):
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

def get_content(url: str):
    content = {}
    text = requests.get(url, headers=headers).text
    content["title"] = filter_text(re.findall('<h2 class="entry-title">(.*)</h2>', text))
    content["case_number"] = filter_text(re.findall('<li class="clearfix ht-kb-pf-standard">案号：(.*)</li>', text))
    content["court"] = filter_text(re.findall('<li class="clearfix ht-kb-pf-standard">法院：(.*)</li>', text))
    content["data"] = filter_text(re.findall('<li class="clearfix ht-kb-pf-standard">时间：(.*)</li>', text))
    content["cause"] = filter_text(re.findall('<li class="clearfix ht-kb-pf-standard">案由：(.*)</li>', text))
    content["type"] = filter_text(re.findall('<li class="clearfix ht-kb-pf-standard">类型：(.*)</li>', text))
    content["procedure"] = filter_text(re.findall('<li class="clearfix ht-kb-pf-standard">程序：(.*)</li>', text))
    content["procedure_explain"] = filter_text(re.findall('<div class="part" id="Explain">\s*<!--.*?-->\s*<p>(.*?)<\/p>\s*<\/div>', text))
    content["tags"] = re.findall('<a href="[^"]+" rel="tag">(.*?)</a>', text) if re.findall('<a href="[^"]+" rel="tag">(.*?)</a>', text) else ""
    content["opinion"] = filter_text(re.findall('<div class="part" id="Opinion">\s*<!--.*?-->\s*<p>(.*?)<\/p>\s*<\/div>', text))
    content["verdict"] = filter_text(re.findall('<div class="part" id="Verdict">\s*<!--.*?-->\s*<p>(.*?)<\/p>\s*<\/div>', text))
    return content

def crawl_contents(links: list, keyword):
    contents = []
    for url in tqdm.tqdm(links):
        print(f"正在爬取内容:{url}")
        content = get_content(url)
        contents.append(content)
        time.sleep(2)
    print(f"======内容爬取完成======")
    # 保存
    with open(f"./data/{keyword}_contents.json", "w", encoding="utf-8") as f:
        json.dump(contents, f, ensure_ascii=False)


if __name__ == "__main__":
    # 1. 爬取链接,保存到 f'./data/{keyword}_links.csv' 下
    crawl_links(strat_page, end_page, keyword)

    # 2. 读取data文件夹下的csv文件里的链接
    file = f"./data/{keyword}_links.csv"
    with open(file, "r", encoding="utf-8") as f:
        links = f.readlines()
        links = [link.strip() for link in links]

    # 3. 根据链接，爬取内容,保存为json文件
    crawl_contents(links, keyword)

    # 4. 读取json并转化成DataFrame
    file = f"./data/{keyword}_contents.json"
    with open(file, "r", encoding="utf-8") as f:
        contents = json.load(f)
    df = pd.DataFrame(contents)
    # 修改标题
    df.rename(columns={"title": "标题", "case_number": "案号", "court": "法院", "data": "日期", "cause": "案由", "type": "类型", "procedure": "程序", "procedure_explain": "程序说明", "tags": "标签", "opinion": "观点", "verdict": "判决"}, inplace=True)
    # 保存到excel
    df.to_excel(f"./data/{keyword}_contents.xlsx", index=False)
    print(f"======保存完成======")






