from src.spider import OpenLawSpider
from src.analysis import Analyzer
from src.utils import read_config

def main():
    # 读取配置文件
    config = read_config()
    cookie = config["cookie"]
    user_agent = config["user_agent"]
    keyword = config["keyword"]
    strat_page = config["strat_page"]
    end_page = config["end_page"]

    # 数据爬取
    spider = OpenLawSpider(keyword, strat_page, end_page, cookie, user_agent)
    # 1. 爬取链接,保存为csv文件
    if spider.crawl_links(): # 如果爬取成功
        # 2. 根据链接，爬取内容,保存为json文件
        spider.crawl_contents()
        # 3. 把json文件转换成excel文件，以便于用户查看
        # spider.save_to_excel()

        # 数据分析
        analyzer = Analyzer(keyword)
        analyzer.auto_analysis()

if __name__ == "__main__":
    main()