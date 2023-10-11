import streamlit as st
import pandas as pd
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import xlsxwriter


from src.utils import set_env
set_env()

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

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def set_session_state_step(i):
    st.session_state.step = i


async def main():
    if "step" not in st.session_state:
        st.session_state.step = 0

    config = {}
    if st.session_state.step >= 0:
        st.title("📖OpenLaw爬取助手")
        config["关键词"] = st.text_input("关键词", placeholder="请输入关键词")
        config["案件类型"] = st.selectbox("案件类型", list(LITIGATION_TYPE_MAP.keys()))
        config["法院（地区）"] = st.selectbox("法院（地区）", list(ZONE_MAP.keys()))
        config["法院层级"] = st.selectbox("法院层级", list(COURT_LEVEL_MAP.keys()))
        config["审判程序"] = st.selectbox("审判程序", list(PROCEDURE_TYPE_MAP.keys()))
        config["文书类型"] = st.selectbox("文书类型", list(DOC_TYPE_MAP.keys()))
        config["判决结果"] = st.selectbox("判决结果", list(JUDGE_RESULT_MAP.keys()))
        config["cookie"] = st.text_input(
            "cookie", "SESSION=MzQxMTMyYjEtMjBkZC00NzQ0LWI0N2EtNzUyYjQzZDA4NDA2"
        )
        config[
            "user_agent"
        ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        start, end = st.columns(2)
        with start:
            config["判决开始时间"] = st.date_input("判决开始时间", date(2011, 1, 1))
        with end:
            config["判决结束时间"] = st.date_input("判决结束时间", datetime.now())
        page_num = st.number_input("您希望至少有多少返回结果（一页20条结果）", 1, None, 100, 20)
        if page_num:
            config["start_page"] = 1
            config["end_page"] = (page_num-1) // 20 + 1

        st.button(
            "😀开始分析",
            on_click=set_session_state_step,
            args=(1,),
            use_container_width=True,
        )
    if st.session_state.step >= 1:
        timer = Timer("timer", logger=None)
        timer.start()
        async with aiohttp.ClientSession() as session:
            # 数据爬取
            spider = OpenLawSpider(
                config,
                session=session,
                concurrent=50,
            )
            with st.spinner("正在爬取链接🔗..."):
                # 1. 爬取链接,保存为csv文件
                have_links = await spider.crawl_links()

            if have_links:  # 如果爬取成功
                st.header("爬取链接成功")
                st.json(spider.links, expanded=False)

                with st.spinner("正在爬取内容..."):
                    await spider.crawl_contents()
                timer.stop()
                st.success(f"😀爬取完成，耗时{timer.last:.2f}秒")
                st.subheader("基础分析结果")
                for key, value in spider.analysis.items():
                    st.markdown(f"**{key}**")
                    if key == "标签":
                        st.json(value, expanded=False)
                    else:
                        st.json(value, expanded=True)

                # ai提取
                with st.spinner("正在AI提取信息，请耐心等待..."):
                    await spider.ai_process()
                st.subheader("AI提取信息成功")
                
                df_xlsx = to_excel(spider.df)
                file_name = spider.base_dir + ".xlsx"
                st.download_button(label='📥 下载结果',
                                                data=df_xlsx ,
                                                file_name= file_name)
                st.header(f"爬取内容成功[共{len(spider.contents)}条]")
                for content in spider.contents:
                    st.json(content, expanded=True)


if __name__ == "__main__":
    asyncio.run(main())
