import requests, bs4, re, os, time, tqdm, csv, json
import pandas as pd

keyword = "个人信息侵权"

if __name__ == "__main__":
    # 读取json并转化成DataFrame
    file = f"./data/{keyword}_contents.json"
    with open(file, "r", encoding="utf-8") as f:
        contents = json.load(f)
    df = pd.DataFrame(contents)
    # 修改标题
    df.rename(columns={"title": "标题", "case_number": "案号", "court": "法院", "data": "日期", "cause": "案由", "type": "类型", "procedure": "程序", "procedure_explain": "程序说明", "tags": "标签", "opinion": "观点", "verdict": "判决"}, inplace=True)

