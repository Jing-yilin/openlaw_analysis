from openlaw_spider import OpenLawSpider
from utils.file_control import read_config

if __name__ == "__main__":
    # 读取配置文件
    config = read_config()
    cookie = config["cookie"]
    user_agent = config["user_agent"]
    search_keyword = config["search_keyword"]
    strat_page = config["strat_page"]
    end_page = config["end_page"]

    # 初始化爬虫
    spider = OpenLawSpider(search_keyword, strat_page, end_page, cookie, user_agent)
    # 1. 爬取链接,保存为csv文件
    if spider.crawl_links(): # 如果爬取成功
        # 2. 根据链接，爬取内容,保存为json文件
        spider.crawl_contents()
        # 3. 把json文件转换成excel文件
        spider.save_to_excel()

    # 数据分析
