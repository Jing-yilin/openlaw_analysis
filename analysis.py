import os
import json
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns

province_city_dic = {
    "北京": ["北京"],
    "上海": ["上海"],
    "深圳": ["深圳"],
    "天津": ["天津"],
    "重庆": ["重庆"],
    "澳门": ["澳门"],
    "香港": ["香港"],
    "海南": ["海口", "三亚"],
    "台湾": ["台湾", "台北", "高雄", "基隆", "台中", "台南", "新竹", "嘉义"],
    "河北": ["唐山", "邯郸", "邢台", "保定", "承德", "沧州", "廊坊", "衡水", "石家庄", "秦皇岛", "张家口"],
    "山西": ["太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁"],
    "山东": [
        "济南",
        "青岛",
        "淄博",
        "枣庄",
        "东营",
        "烟台",
        "潍坊",
        "济宁",
        "泰安",
        "威海",
        "日照",
        "莱芜",
        "临沂",
        "德州",
        "聊城",
        "滨州",
        "荷泽",
        "菏泽",
    ],
    "江苏": [
        "南京",
        "无锡",
        "徐州",
        "常州",
        "苏州",
        "南通",
        "淮安",
        "盐城",
        "扬州",
        "镇江",
        "泰州",
        "宿迁",
        "连云港",
    ],
    "浙江": ["杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"],
    "安徽": [
        "合肥",
        "芜湖",
        "蚌埠",
        "淮南",
        "淮北",
        "铜陵",
        "安庆",
        "黄山",
        "滁州",
        "阜阳",
        "宿州",
        "巢湖",
        "六安",
        "亳州",
        "池州",
        "宣城",
        "马鞍山",
    ],
    "福建": ["福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德"],
    "江西": ["南昌", "萍乡", "新余", "九江", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶", "景德镇"],
    "河南": [
        "郑州",
        "开封",
        "洛阳",
        "焦作",
        "鹤壁",
        "新乡",
        "安阳",
        "濮阳",
        "许昌",
        "漯河",
        "南阳",
        "商丘",
        "信阳",
        "周口",
        "驻马店",
        "济源",
        "平顶山",
        "三门峡",
    ],
    "湖北": [
        "武汉",
        "黄石",
        "襄樊",
        "十堰",
        "荆州",
        "宜昌",
        "荆门",
        "鄂州",
        "孝感",
        "黄冈",
        "咸宁",
        "随州",
        "恩施",
        "仙桃",
        "天门",
        "潜江",
    ],
    "湖南": [
        "长沙",
        "株洲",
        "湘潭",
        "衡阳",
        "邵阳",
        "岳阳",
        "常德",
        "益阳",
        "郴州",
        "永州",
        "怀化",
        "娄底",
        "吉首",
        "张家界",
    ],
    "广东": [
        "广州",
        "深圳",
        "珠海",
        "汕头",
        "韶关",
        "佛山",
        "江门",
        "湛江",
        "茂名",
        "肇庆",
        "惠州",
        "梅州",
        "汕尾",
        "河源",
        "阳江",
        "清远",
        "东莞",
        "中山",
        "潮州",
        "揭阳",
        "云浮",
    ],
    "广西": [
        "南宁",
        "柳州",
        "桂林",
        "梧州",
        "北海",
        "钦州",
        "贵港",
        "玉林",
        "百色",
        "贺州",
        "河池",
        "来宾",
        "崇左",
        "防城港",
    ],
    "四川": [
        "成都",
        "自贡",
        "泸州",
        "德阳",
        "绵阳",
        "广元",
        "遂宁",
        "内江",
        "乐山",
        "南充",
        "宜宾",
        "广安",
        "达州",
        "眉山",
        "雅安",
        "巴中",
        "资阳",
        "西昌",
        "攀枝花",
    ],
    "贵州": [
        "贵阳",
        "遵义",
        "安顺",
        "铜仁",
        "毕节",
        "兴义",
        "凯里",
        "都匀",
        "六盘水",
        "黔西南布依族苗族自治州",
        "黔东南苗族侗族自治州",
        "黔南布依族苗族自治州",
    ],
    "云南": ["昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "思茅", "临沧", "景洪", "楚雄", "大理", "潞西"],
    "陕西": ["西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛"],
    "甘肃": [
        "兰州",
        "金昌",
        "白银",
        "天水",
        "武威",
        "张掖",
        "平凉",
        "酒泉",
        "庆阳",
        "定西",
        "陇南",
        "临夏",
        "合作",
        "嘉峪关",
    ],
    "辽宁": [
        "沈阳",
        "大连",
        "鞍山",
        "抚顺",
        "本溪",
        "丹东",
        "锦州",
        "营口",
        "盘锦",
        "阜新",
        "辽阳",
        "铁岭",
        "朝阳",
        "葫芦岛",
    ],
    "吉林": ["长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延吉"],
    "黑龙江": [
        "鹤岗",
        "鸡西",
        "大庆",
        "伊春",
        "黑河",
        "绥化",
        "双鸭山",
        "牡丹江",
        "佳木斯",
        "七台河",
        "哈尔滨",
        "齐齐哈尔",
    ],
    "青海": ["西宁", "德令哈", "格尔木"],
    "宁夏": ["银川", "吴忠", "固原", "中卫", "石嘴山"],
    "西藏": ["拉萨", "日喀则"],
    "新疆": [
        "哈密",
        "和田",
        "喀什",
        "昌吉",
        "博乐",
        "伊宁",
        "塔城",
        "吐鲁番",
        "阿图什",
        "库尔勒",
        "五家渠",
        "阿克苏",
        "阿勒泰",
        "石河子",
        "阿拉尔",
        "乌鲁木齐",
        "克拉玛依",
        "图木舒克",
    ],
    "内蒙古": [
        "包头",
        "乌海",
        "赤峰",
        "通辽",
        "鄂尔多斯",
        "呼伦贝尔",
        "巴彦淖尔",
        "乌兰察布",
        "兴安盟",
        "呼和浩特",
        "锡林郭勒盟",
        "阿拉善盟",
        "巴彦淖尔盟",
        "乌兰察布盟",
    ],
}


def read_content(keyword, sort_by_data=True):
    # 读取json并转化成DataFrame
    file = f"./data/{keyword}_contents.json"
    with open(file, "r", encoding="utf-8") as f:
        contents = json.load(f)
    df = pd.DataFrame(contents)
    # 修改标题
    df.rename(
        columns={
            "title": "标题",
            "case_number": "案号",
            "court": "法院",
            "data": "日期",
            "cause": "案由",
            "type": "类型",
            "procedure": "程序",
            "procedure_explain": "程序说明",
            "tags": "标签",
            "opinion": "观点",
            "verdict": "判决",
        },
        inplace=True,
    )
    # 转换日期格式 2020年06月10日 -> 2020-06-10
    df["日期"] = df["日期"].apply(
        lambda x: x.replace("年", "-").replace("月", "-").replace("日", "")
    )
    # 改变日期数据类型
    df["日期"] = pd.to_datetime(df["日期"])
    df.sort_values(by="日期", inplace=True)
    return df


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


def read_law_dic(path) -> list:
    # 读取法律词典
    with open(path, "r", encoding="utf-8") as f:
        law_dic = f.readlines()
    # 去除换行符
    law_dic = [law.strip() for law in law_dic]
    return law_dic


def sort_dict_by_value(dic: dict, start=0, end=10, desc=True) -> dict:
    """根据字典的值排序，默认降序"""
    return dict(sorted(dic.items(), key=lambda x: x[1], reverse=desc)[start:end])


def draw_word_cloud_by_freq(
    word_freq, save_path, file_name, w=1000, h=500, dpi=300
) -> None:
    # 清空画布
    plt.clf()
    # 根据词频绘制词云
    wc = WordCloud(
        font_path="./fonts/微软雅黑.ttf", background_color="white", width=w, height=h
    )
    wc.generate_from_frequencies(word_freq)
    plt.imshow(wc)
    plt.axis("off")
    plt.savefig(save_path + "/" + file_name, dpi=dpi)


def draw_barh(
    dic,
    save_path,
    file_name,
    x_label,
    y_label,
    title,
    w=1000,
    h=500,
    dpi=300,
    rotation=45,
    grid=True,
    tight=True,
) -> None:
    plt.clf()
    plt.title(title)
    plt.figure(figsize=(10, 5), dpi=dpi)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.yticks(rotation=rotation)
    plt.grid(grid)
    sns.barplot(x=list(dic.values()), y=list(dic.keys()))
    plt.savefig(
        save_path + "/" + file_name, dpi=dpi, bbox_inches="tight" if tight else None
    )


def draw_bar(
    dic,
    save_path,
    file_name,
    x_label,
    y_label,
    title,
    w=1000,
    h=500,
    dpi=300,
    rotation=45,
    grid=True,
    tight=True,
) -> None:
    plt.clf()
    plt.grid(grid)
    plt.figure(figsize=(10, 5), dpi=dpi)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=rotation)
    plt.title(title)
    sns.barplot(x=list(dic.keys()), y=list(dic.values()))
    plt.savefig(
        save_path + "/" + file_name, dpi=dpi, bbox_inches="tight" if tight else None
    )


if __name__ == "__main__":
    keyword = "网络个人信息侵权"  # 关键词
    law_dic_path = "./dic/law_dic.txt"  # 法律词典路径
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 设置字体
    save_path = f"./result/{keyword}"  # 保存路径
    plt.figure(figsize=(10, 5), dpi=300)  # 设置图片大小和分辨率
    sns.set_color_codes(palette='muted') # 设置配色

    law_dic_count = {}  # 记录法条词频
    cause_count = {}  # 记录案由词频
    tag_count = {}  # 记录标签词频
    year_count = {}  # 记录年份词频

    df = read_content(keyword, sort_by_data=True)
    create_dir(save_path)
    law_dic = read_law_dic(law_dic_path)

    # 1. 统计法条词频
    for law in law_dic:
        law_dic_count[law] = df["判决"].apply(lambda x: x.count(law)).sum()
    law_dic_count = dict(
        sorted(law_dic_count.items(), key=lambda x: x[1], reverse=True)
    )
    draw_word_cloud_by_freq(law_dic_count, save_path, f"{keyword}_法条词云.png")
    draw_barh(
        sort_dict_by_value(law_dic_count),
        save_path,
        f"{keyword}_法条词频.png",
        "词频",
        "法条",
        f"{keyword}法条词频",
    )

    # 2. 统计案由词频
    for cause in df["案由"]:
        cause_count[cause] = df["案由"].apply(lambda x: x.count(cause)).sum()
    draw_word_cloud_by_freq(cause_count, save_path, f"{keyword}_案由词云.png")
    draw_barh(
        sort_dict_by_value(cause_count),
        save_path,
        f"{keyword}_案由词频.png",
        "词频",
        "案由",
        f"{keyword}案由词频",
    )

    # 3. 统计标签词频
    tags = []
    for tag in df["标签"]:
        tags.extend(tag)
    for tag in tags:
        tag_count[tag] = tags.count(tag)
    draw_word_cloud_by_freq(tag_count, save_path, f"{keyword}_标签词云.png")
    draw_barh(
        sort_dict_by_value(tag_count),
        save_path,
        f"{keyword}_标签词频.png",
        "词频",
        "标签",
        f"{keyword}标签词频",
    )

    # 4. 统计年份词频
    year_count = df["日期"].apply(lambda x: x.year).value_counts().to_dict()
    draw_bar(
        year_count,
        save_path,
        f"{keyword}_案件数量随时间变化.png",
        "年份",
        "案件数量",
        f"{keyword}案件数量随时间变化",
    )


    court_count = {}
    # 所有省份初始化为0
    for province in province_city_dic.keys():
        court_count[province] = 0

    for court in df["法院"].value_counts()[df["法院"].value_counts() > 3].index:
        # 如果key是“重庆”开头，则加入的是“重庆”对应的value
        for province in province_city_dic.keys():
            if court.startswith(province[:2]):
                court_count[province] += df["法院"].value_counts()[court]
                break
    print(court_count)