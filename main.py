import asyncio
import aiohttp
from codetiming import Timer
from src.spider import OpenLawSpider
from src.analysis import Analyzer
from src.utils import read_config




async def main():
    # 读取配置文件
    config = read_config()

    with Timer(text="总耗时: {:.1f} s"):
        # 创建session
        async with aiohttp.ClientSession() as session:
            # 数据爬取
            spider = OpenLawSpider(
                config,
                session=session,
                concurrent=10,
            )
            # 1. 爬取链接,保存为csv文件
            if await spider.crawl_links():  # 如果爬取成功
                # 2. 根据链接，爬取内容,保存为json文件
                await spider.crawl_contents()
                # 3. 把json文件转换成excel文件，以便于用户查看
                spider.save_to_excel()

                # 数据分析
                analyzer = Analyzer(config)
                analyzer.auto_analysis()


if __name__ == "__main__":
    asyncio.run(main())
