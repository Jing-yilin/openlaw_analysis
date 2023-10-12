import streamlit as st
import asyncio
import aiohttp
from codetiming import Timer

from src.utils import set_env, to_excel
from datetime import date, datetime
from src.spider import OpenLawSpider, login_openlaw
from src.analysis import Analyzer
from src.utils import read_config
from src.spider.openlaw_spider import (
    DOC_TYPE_MAP,
    PROCEDURE_TYPE_MAP,
    COURT_LEVEL_MAP,
    JUDGE_RESULT_MAP,
    LITIGATION_TYPE_MAP,
    ZONE_MAP,
)

set_env()

def set_session_state_step(i):
    st.session_state.step = i


async def main():
    if "step" not in st.session_state:
        st.session_state.step = 0

    config = {}
    if st.session_state.step >= 0:
        st.title("📖OpenLaw爬取助手")
        ai_mode = st.checkbox("AI模式")
        openai_sk = st.text_input("OpenAI SK", type="password", disabled=not ai_mode)
        username = st.text_input("用户名", placeholder="请输入openlaw的用户名", value="1154896650@qq.com")
        password = st.text_input("密码", type="password", placeholder="请输入openlaw的密码", value="3.1415926Jj302")
        config["关键词"] = st.text_input("关键词", placeholder="请输入关键词", value="房屋租赁")
        config["案件类型"] = st.selectbox("案件类型", list(LITIGATION_TYPE_MAP.keys()))
        config["法院（地区）"] = st.selectbox("法院（地区）", list(ZONE_MAP.keys()))
        config["法院层级"] = st.selectbox("法院层级", list(COURT_LEVEL_MAP.keys()))
        config["审判程序"] = st.selectbox("审判程序", list(PROCEDURE_TYPE_MAP.keys()))
        config["文书类型"] = st.selectbox("文书类型", list(DOC_TYPE_MAP.keys()))
        config["判决结果"] = st.selectbox("判决结果", list(JUDGE_RESULT_MAP.keys()))
        
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
            config["end_page"] = (page_num - 1) // 20 + 1

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
            # 登录
            with st.spinner("正在登录..."):
                config["cookie"] = await login_openlaw(username, password, session)
            # 数据爬取
            spider = OpenLawSpider(
                config,
                session=session,
                concurrent=50,
                ai_mode=ai_mode,
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

                df_xlsx = to_excel(spider.df)
                file_name = spider.base_dir + ".xlsx"
                st.download_button(label="📥 下载结果", data=df_xlsx, file_name=file_name)
                st.header(f"爬取内容成功[共{len(spider.contents)}条]")
                for content in spider.contents:
                    st.markdown(f"**{content['标题']}**")
                    st.json(content, expanded=False)

                # ai提取
                if ai_mode:
                    with st.spinner("正在AI提取信息，请耐心等待..."):
                        await spider.ai_process()
                    st.subheader("AI提取信息成功")


if __name__ == "__main__":
    asyncio.run(main())
