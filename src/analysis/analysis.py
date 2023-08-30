import os
import json
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
import yaml
import pathlib

from ..utils import create_dir, read_config

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


class Analyzer:
    def __init__(self, keyword, law_dic_path="./dic/law_dic.txt") -> None:
        self.keyword = keyword
        self.content = None
        self.law_dic_path = law_dic_path
        self.read_law_dic()
        self.save_dir = str(pathlib.Path.cwd() / "result" / self.keyword).replace("\\", "/")
        create_dir(self.save_dir)

    def read_content(self, sort_by_data=True) -> None:
        # 读取json并转化成DataFrame
        file = f"./data/{self.keyword}/{self.keyword}_contents.json"
        with open(file, "r", encoding="utf-8") as f:
            contents = json.load(f)
        df = pd.DataFrame(contents)
        # 修改标题
        df.rename(
            columns={
                "url": "链接",
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
        self.content = df
        print("=======成功读取数据！=======")
        print(f"=======共有{len(df)}条数据=======")

    def read_law_dic(self) -> None:
        # 读取法律词典
        with open(self.law_dic_path, "r", encoding="utf-8") as f:
            law_dic = f.readlines()
        # 去除换行符
        law_dic = [law.strip() for law in law_dic]
        self.law_dic = law_dic

    def sort_dict_by_value(self, dic: dict, start=0, end=10, desc=True) -> dict:
        """根据字典的值排序，默认降序"""
        return dict(sorted(dic.items(), key=lambda x: x[1], reverse=desc)[start:end])

    def draw_word_cloud_by_freq(
        self, word_freq, file_name, w=1000, h=500, dpi=300
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
        plt.savefig(self.save_dir + "/" + file_name, dpi=dpi)

    def draw_barh(
        self,
        dic,
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
            self.save_dir + "/" + file_name,
            dpi=dpi,
            bbox_inches="tight" if tight else None,
        )

    def draw_bar(
        self,
        dic,
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
            self.save_dir + "/" + file_name,
            dpi=dpi,
            bbox_inches="tight" if tight else None,
        )

    def analyze_law(self) -> None:
        law_dic_count = {}
        for law in self.law_dic:
            law_dic_count[law] = self.content["判决"].apply(lambda x: x.count(law)).sum()
        law_dic_count = dict(
            sorted(law_dic_count.items(), key=lambda x: x[1], reverse=True)
        )
        self.draw_word_cloud_by_freq(law_dic_count, f"{self.keyword}_法条词云.png")
        self.draw_barh(
            self.sort_dict_by_value(law_dic_count),
            f"{self.keyword}_法条词频.png",
            "词频",
            "法条",
            f"{self.keyword}法条词频",
        )

    def analyze_cause(self) -> None:
        cause_count = {}
        for cause in self.content["案由"]:
            cause_count[cause] = (
                self.content["案由"].apply(lambda x: x.count(cause)).sum()
            )
        self.draw_word_cloud_by_freq(cause_count, f"{self.keyword}_案由词云.png")
        self.draw_barh(
            self.sort_dict_by_value(cause_count),
            f"{self.keyword}_案由词频.png",
            "词频",
            "案由",
            f"{self.keyword}案由词频",
        )

    def analyze_tag(self) -> None:
        tag_count = {}
        tags = []
        for tag in self.content["标签"]:
            tags.extend(tag)
        for tag in tags:
            tag_count[tag] = tags.count(tag)
        self.draw_word_cloud_by_freq(tag_count, f"{self.keyword}_标签词云.png")
        self.draw_barh(
            self.sort_dict_by_value(tag_count),
            f"{self.keyword}_标签词频.png",
            "词频",
            "标签",
            f"{self.keyword}标签词频",
        )

    def analyze_year(self) -> None:
        year_count = self.content["日期"].apply(lambda x: x.year).value_counts().to_dict()
        self.draw_bar(
            year_count,
            f"{self.keyword}_案件数量随时间变化.png",
            "年份",
            "案件数量",
            f"{self.keyword}案件数量随时间变化",
        )

    def auto_analysis(self) -> None:
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 设置字体
        plt.figure(figsize=(10, 5), dpi=300)  # 设置图片大小和分辨率
        sns.set_color_codes(palette="muted")  # 设置配色
        self.read_content()
        print("=======开始分析=======")
        self.analyze_law()
        print("- 法条分析完成")
        self.analyze_cause()
        print("- 案由分析完成")
        self.analyze_tag()
        print("- 标签分析完成")
        self.analyze_year()
        print("- 年份分析完成")
        print(f"=======分析完成，可查看 {self.save_dir} 文件夹=======")
