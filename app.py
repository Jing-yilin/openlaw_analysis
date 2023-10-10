import streamlit as st
from datetime import date, datetime
from src.spider.openlaw_spider import (
    DOC_TYPE_MAP,
    PROCEDURE_TYPE_MAP,
    COURT_LEVEL_MAP,
    JUDGE_RESULT_MAP,
    LITIGATION_TYPE_MAP,
    ZONE_MAP,
)

import asyncio
import aiohttp
from codetiming import Timer
from src.spider import OpenLawSpider
from src.analysis import Analyzer
from src.utils import read_config


def set_session_state_step(i):
    st.session_state.step = i


async def main():
    if "step" not in st.session_state:
        st.session_state.step = 0

    config = {}
    if st.session_state.step >= 0:
        st.title("裁判文书网分析助手")
        config["关键词"] = st.text_input("关键词")
        config["案件类型"] = st.selectbox("案件类型", list(LITIGATION_TYPE_MAP.keys()))
        config["法院（地区）"] = st.selectbox("法院（地区）", list(ZONE_MAP.keys()))
        config["法院层级"] = st.selectbox("法院层级", list(COURT_LEVEL_MAP.keys()))
        config["审判程序"] = st.selectbox("审判程序", list(PROCEDURE_TYPE_MAP.keys()))
        config["文书类型"] = st.selectbox("文书类型", list(DOC_TYPE_MAP.keys()))
        config["判决结果"] = st.selectbox("判决结果", list(JUDGE_RESULT_MAP.keys()))
        config["cookie"] = st.text_input(
            "cookie", "SESSION=NTk4ZWFkZTktMzkwNy00NjZmLWIxNGMtOGM0MDRlOTA2ZDYx"
        )
        config[
            "user_agent"
        ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        start, end = st.columns(2)
        with start:
            config["判决开始时间"] = st.date_input("判决开始时间", date(2011, 1, 1))
        with end:
            config["判决结束时间"] = st.date_input("判决结束时间", datetime.now())
        start_page, end_page = st.columns(2)
        with start_page:
            config["strat_page"] = st.number_input("开始页码", 1)
        with end_page:
            config["end_page"] = st.number_input("结束页码", 1)

        st.button(
            "😀开始分析",
            on_click=set_session_state_step,
            args=(1,),
            use_container_width=True,
        )
    if st.session_state.step >= 1:
        async with aiohttp.ClientSession() as session:
            # 数据爬取
            spider = OpenLawSpider(
                config,
                session=session,
                concurrent=4,
            )
            with st.spinner("正在爬取链接🔗..."):
                # 1. 爬取链接,保存为csv文件
                have_links = await spider.crawl_links()

            if have_links:  # 如果爬取成功
                st.header("爬取链接成功")
                st.json(spider.links, expanded=False)

                with st.spinner("正在爬取内容..."):
                    # 2. 根据链接，爬取内容,保存为json文件
                    await spider.crawl_contents()
                st.header(f"爬取内容成功[共{len(spider.contents)}条]")
                for content in spider.contents:
                    st.json(content, expanded=True)
                # 3. 把json文件转换成excel文件，以便于用户查看
                spider.save_to_excel()

                # 数据分析
                # analyzer = Analyzer(config)
                # analyzer.auto_analysis()


if __name__ == "__main__":
    asyncio.run(main())
