# 项目说明
该项目是一个针对[openlaw](http://openlaw.cn/index.jsp)网站的爬虫
所有的基础配置都可以在`config.py`中进行配置

## 配置说明

- username: 登录用户名
- password: 登录密码
- user_agent: 浏览器的型号，可以不用改
- cookie: 从浏览器中获取的cookie，会动态的变化，如果失效了需要重新获取
- search_keyword: 在`openlaw_spider.py`搜索的关键词
- analysis_keyword: 在`data_analysis.py`中分析的关键词
- strat_page: 开始爬取的页数
- end_page: 结束爬取的页数

# 运行项目
## 1. 安装依赖
在terminal中运行一下命令，安装依赖
```shell
pip install -r requirements.txt
```
## 2.修改配置文件
在`config.py`中修改配置文件，修改为目标的关键词以及爬取的页数，以及要分析的关键词
## 2. 运行爬虫
```shell
python main.py
```

数据将会被存储在 `./data` 目录下
分析产生的可视化文件将被存储在 `./result` 目录下



