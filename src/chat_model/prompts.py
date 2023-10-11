from langchain.prompts.prompt import PromptTemplate

_law_result_template = """现在你是一个帮助分析法律判决结果的助手，你的工作是从法律判决文书中提取出:
1.原告起诉的事实与理由
2.原告起诉的法律依据（精确到条数），使用list形式
3.原告起诉的诉讼请求
4.被告辩称的事实与理由
5.被告辩称的法律依据（精确到条数），使用list形式
6.法院认定和查明的事实
7.法院的判决的法律依据（精确到条数），使用list形式
8.法院的判决结果

输入:
庭审程序说明: 
```{explain}```
庭审过程: 
```{procedure}```
查明事实: 
```{facts}```
法院意见: 
```{opinion}```

输出（请采用json格式）:
```
{{
    "原告起诉的事实与理由": 
    "原告起诉的法律依据": 
    "原告起诉的诉讼请求": 
    "被告辩称的事实与理由": 
    "被告辩称的法律依据": 
    "法院认定和查明的事实": 
    "法院的判决的法律依据": 
    "法院的判决结果": 
}}
```
如果没有找到则留空。
"""

LAW_RESULT_TEMPLATE = PromptTemplate.from_template(_law_result_template)