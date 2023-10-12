import os
import yaml
import pandas as pd
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import xlsxwriter

def read_config(file_name="config.yaml") -> dict:
    # 读取config.yaml文件
    with open(file_name, "r", encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def create_dir(dir_name) -> None:
    # 拆分 dir_name
    dir_names = dir_name.split("/")
    # 创建文件夹
    for i in range(len(dir_names)):
        path = "/".join(dir_names[: i + 1])
        if path == "" or path == ".":
            continue
        if not os.path.exists(path):
            os.mkdir(path)

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