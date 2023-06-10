import os
import yaml

def read_config(file_name="config.yaml"):
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

