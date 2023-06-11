from openlaw_spider import OpenLawSpider
from analysis import Analyzer
from utils.file_control import read_config

if __name__ == "__main__":
    # 读取配置文件
    config = read_config()
    cookie = config["cookie"]
    user_agent = config["user_agent"]
    search_keyword = config["search_keyword"]
    analysis_keyword = config["analysis_keyword"]
    strat_page = config["strat_page"]
    end_page = config["end_page"]

    # 数据爬取
    spider = OpenLawSpider(search_keyword, strat_page, end_page, cookie, user_agent)
    # 1. 爬取链接,保存为csv文件
    if spider.crawl_links(): # 如果爬取成功
        # 2. 根据链接，爬取内容,保存为json文件
        spider.crawl_contents()
        # 3. 把json文件转换成excel文件，以便于用户查看
        spider.save_to_excel()

        # 数据分析
        analyzer = Analyzer(keyword=analysis_keyword)
        analyzer.auto_analysis()