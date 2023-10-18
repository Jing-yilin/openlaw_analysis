import streamlit as st
import asyncio
import aiohttp
from codetiming import Timer
import datetime
import pandas as pd
import os

from src.utils import to_excel, create_dir
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

import logging
from logging import Logger

# 初始化日志
create_dir("./logs")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# 创建日志格式化器
formatter = logging.Formatter("[%(asctime)s] - %(name)s - %(levelname)s - %(message)s")

if not logger.hasHandlers():
    # 创建控制台日志处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # 创建文件日志处理器
    fh = logging.FileHandler(f"./logs/{datetime.now().strftime('%Y-%m-%d')}_log.log")
    fh.setLevel(logging.DEBUG)
    # 将日志格式化器添加到日志处理器
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # 将日志处理器添加到日志对象
    logger.addHandler(ch)
    logger.addHandler(fh)

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


async def login_openlaw_st(username, password, logger=logger):
    logger.info("正在登录" f"用户名: {username} " f"密码: {password}")

    # 创建session
    async with aiohttp.ClientSession() as session:
        if await login_openlaw(username, password, session, logger=logger):
            logger.info("✅账号已经登录！")
            st.success("登录成功")
            set_session_state_login(True)
            set_session_state_username(username)
            set_session_state_password(password)
            set_session_state_step(1)
        else:
            logger.info("❎账号登录失败!")
            st.error("登录失败")
            set_session_state_login(False)
            set_session_state_step(0)


async def main(logger: Logger):
    config = {}
    if st.session_state.step >= 0:
        logger.info(f"===== st.session_state.step: {st.session_state.step} =====")
        st.title("📖OpenLaw爬取助手")
        ai_mode = st.checkbox("AI模式")
        openai_sk = st.text_input(
            "OpenAI SK", type="password", value="", disabled=not ai_mode
        )
        # proxy = st.text_input(
        #     "代理", value="http://127.0.0.1:7890", placeholder="http://", disabled=not ai_mode
        # )
        if openai_sk and ai_mode:
            os.environ["OPENAI_API_KEY"] = openai_sk
            logger.info(f"OPENAI_API_KEY: {os.environ['OPENAI_API_KEY']}")
        # if proxy and ai_mode:
        #     os.environ["HTTP_PROXY"] = proxy
        #     os.environ["HTTPS_PROXY"] = proxy

        if not st.session_state.login:
            username = st.text_input("用户名", placeholder="请输入openlaw的用户名", value=None)
            password = st.text_input(
                "密码",
                type="password",
                placeholder="请输入openlaw的密码",
                value=None,
            )
            if username:
                password = "" if password is None else password
                if st.button(
                    "登录",
                    use_container_width=True,
                ):
                    await login_openlaw_st(username, password, logger=logger)
            else:
                st.warning("请输入用户名和密码")
        else:
            logger.info(f"用户[{st.session_state.username}]已经登录啦~")
            st.success(f"用户[{st.session_state.username}]已经登录啦~")

    if st.session_state.step >= 1:
        logger.info(f"===== st.session_state.step: {st.session_state.step} =====")

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
        config["数量"] = st.number_input(
            "您希望至少有多少返回结果（一页20条结果）",
            1,
            None,
            100,
            20,
            on_change=set_session_state_step,
            args=(1,),
        )

        st.button(
            "😀开始分析",
            on_click=set_session_state_step,
            args=(2,),
            use_container_width=True,
        )

    if st.session_state.step >= 2:
        logger.info(f"===== st.session_state.step: {st.session_state.step} =====")

        timer = Timer("timer", logger=None)
        timer.start()
        logger.info("Timer started")
        async with aiohttp.ClientSession() as session:
            logger.info("正在登录...")
            with st.spinner("正在登录..."):
                config["cookie"] = await login_openlaw(
                    st.session_state.username,
                    st.session_state.password,
                    session,
                    logger=logger,
                )
                config["username"] = st.session_state.username
                config["password"] = st.session_state.password
            # 数据爬取
            logger.info("正在初始化OpenLawSpider")
            spider = OpenLawSpider(
                config,
                session=session,
                concurrent=50,
                ai_mode=ai_mode,
                logger=logger
            )
            logger.info("初始化OpenLawSpider成功")
            logger.info("正在爬取链接🔗...")
            with st.spinner("正在爬取链接🔗..."):
                # 1. 爬取链接,保存为csv文件
                have_links = await spider.crawl_links()

            if have_links:  # 如果爬取成功
                st.header("爬取链接成功")
                st.json(spider.links, expanded=False)

                logger.info("正在爬取内容...")
                with st.spinner("正在爬取内容..."):
                    await spider.crawl_contents()
                timer.stop()
                logger.info(f"😀爬取完成，耗时{timer.last:.2f}秒")
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

                # 下载结果
                logger.info("正在串行化数据...")
                df_xlsx = to_excel(spider.df)
                file_name = spider.base_dir + ".xlsx"
                st.download_button(label="📥 下载结果", data=df_xlsx, file_name=file_name)

                logger.info(f"==== 爬取内容成功[共{len(spider.contents)}条] ====")
                st.header(f"爬取内容成功[共{len(spider.contents)}条]")
                with st.expander("👉查看爬取内容", expanded=False):
                    for content in spider.contents:
                        st.markdown(f"**{content['标题']}**")
                        df = pd.DataFrame.from_dict(content, orient="index")
                        df.index.name = "字段"
                        df.columns = ["内容"]
                        st.dataframe(df, use_container_width=True)

                # ai提取
                if ai_mode:
                    with st.spinner("正在AI提取信息，请耐心等待..."):
                        await spider.ai_process()
                    st.subheader("AI提取信息成功")

            else:
                st.error("😭没有找到任何符合条件的链接，请更新参数！")


if __name__ == "__main__":
    asyncio.run(main(logger))
