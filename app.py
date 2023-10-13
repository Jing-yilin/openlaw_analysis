import streamlit as st
import asyncio
import aiohttp
from codetiming import Timer
import pandas as pd
import os

from src.utils import to_excel
from datetime import date, datetime
from src.spider import OpenLawSpider, login_openlaw, check_login_status
from src.spider.openlaw_spider import (
    DOC_TYPE_MAP,
    PROCEDURE_TYPE_MAP,
    COURT_LEVEL_MAP,
    JUDGE_RESULT_MAP,
    LITIGATION_TYPE_MAP,
    ZONE_MAP,
)

if "step" not in st.session_state:
    st.session_state.step = 0
if "login" not in st.session_state:
    st.session_state.login = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "password" not in st.session_state:
    st.session_state.password = ""


def set_session_state_step(i):
    st.session_state.step = i

def set_session_state_login(status):
    st.session_state.login = status


def set_session_state_username(username):
    st.session_state.username = username


def set_session_state_password(password):
    st.session_state.password = password

async def login_openlaw_st(username, password):
    print("======正在登录======\n"
          f"用户名: {username}\n"
          f"密码: {len(password) * '*'}")
    
    # 创建session
    async with aiohttp.ClientSession() as session:
        if await login_openlaw(username, password, session):
            print("✅账号已经登录！")
            st.success("登录成功")
            set_session_state_login(True)
            set_session_state_username(username)
            set_session_state_password(password)
            set_session_state_step(1)
        else:
            print("❎账号登录失败!")
            st.error("登录失败")
            set_session_state_login(False)
            set_session_state_step(0)


async def main():
    config = {}
    if st.session_state.step >= 0:
        st.title("📖OpenLaw爬取助手")
        ai_mode = st.checkbox("AI模式")
        openai_sk = st.text_input(
            "OpenAI SK", type="password", value="", disabled=not ai_mode
        )
        if openai_sk and openai_sk.startswith("sk-"):
            os.environ["OPENAI_API_KEY"] = openai_sk
        if not st.session_state.login:
            username = st.text_input("用户名", placeholder="请输入openlaw的用户名", value=None)
            password = st.text_input(
                "密码",
                type="password",
                placeholder="请输入openlaw的密码",
                value=None,
            )
            if username and password:
                if st.button(
                    "登录",
                    use_container_width=True,
                ):
                    await login_openlaw_st(username, password)
            else:
                st.warning("请输入用户名和密码")
        else:
            st.success(f"用户[{st.session_state.username}]已经登录啦~")

    if st.session_state.step >= 1:
        config["关键词"] = st.text_input(
            "关键词",
            placeholder="请输入关键词",
            value="房屋租赁",
            on_change=set_session_state_step,
            args=(1,),
        )
        config["案件类型"] = st.selectbox(
            "案件类型",
            list(LITIGATION_TYPE_MAP.keys()),
            on_change=set_session_state_step,
            args=(1,),
        )
        config["法院（地区）"] = st.selectbox(
            "法院（地区）", list(ZONE_MAP.keys()), on_change=set_session_state_step, args=(1,)
        )
        config["法院层级"] = st.selectbox(
            "法院层级",
            list(COURT_LEVEL_MAP.keys()),
            on_change=set_session_state_step,
            args=(1,),
        )
        config["审判程序"] = st.selectbox(
            "审判程序",
            list(PROCEDURE_TYPE_MAP.keys()),
            on_change=set_session_state_step,
            args=(1,),
        )
        config["文书类型"] = st.selectbox(
            "文书类型",
            list(DOC_TYPE_MAP.keys()),
            on_change=set_session_state_step,
            args=(1,),
        )
        config["判决结果"] = st.selectbox(
            "判决结果",
            list(JUDGE_RESULT_MAP.keys()),
            on_change=set_session_state_step,
            args=(1,),
        )

        config[
            "user_agent"
        ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        start, end = st.columns(2)
        with start:
            config["判决开始时间"] = st.date_input(
                "判决开始时间", date(2011, 1, 1), on_change=set_session_state_step, args=(1,)
            )
        with end:
            config["判决结束时间"] = st.date_input(
                "判决结束时间", datetime.now(), on_change=set_session_state_step, args=(1,)
            )
        page_num = st.number_input(
            "您希望至少有多少返回结果（一页20条结果）",
            1,
            None,
            100,
            20,
            on_change=set_session_state_step,
            args=(1,),
        )
        if page_num:
            config["start_page"] = 1
            config["end_page"] = (page_num - 1) // 20 + 1

        st.button(
            "😀开始分析",
            on_click=set_session_state_step,
            args=(2,),
            use_container_width=True,
        )

    if st.session_state.step >= 2:
        timer = Timer("timer", logger=None)
        print("Timer started")
        timer.start()
        async with aiohttp.ClientSession() as session:
            with st.spinner("正在登录..."):
                config["cookie"] = await login_openlaw(
                    st.session_state.username, st.session_state.password, session
                )
                config["username"] = st.session_state.username
                config["password"] = st.session_state.password
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

                # side显示基础的统计结果
                with st.sidebar:
                    st.subheader("基础分析结果")
                    for key, value in spider.analysis.items():
                        st.markdown(f"**{key}**")

                        df = pd.DataFrame.from_dict(value, orient="index")
                        df.columns = ["数量"]
                        df.index.name = key
                        df.sort_values(by="数量", ascending=False, inplace=True)
                        st.dataframe(df, use_container_width=True)

                df_xlsx = to_excel(spider.df)
                file_name = spider.base_dir + ".xlsx"
                st.download_button(label="📥 下载结果", data=df_xlsx, file_name=file_name)
                st.header(f"爬取内容成功[共{len(spider.contents)}条]")
                for content in spider.contents:
                    st.markdown(f"**{content['标题']}**")
                    df = pd.DataFrame.from_dict(content, orient="index")
                    df.index.name = "字段"
                    st.dataframe(df, use_container_width=True)


                # ai提取
                if ai_mode:
                    with st.spinner("正在AI提取信息，请耐心等待..."):
                        await spider.ai_process()
                    st.subheader("AI提取信息成功")

            else:
                st.error("😭没有找到任何符合条件的链接，请更新参数！")


if __name__ == "__main__":
    asyncio.run(main())
