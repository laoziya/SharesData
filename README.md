
- 1. [使用介绍](#1-使用介绍)
- 2. [网站分析](#2-网站分析)
    - 2.1. [行业板块页面](#21-行业板块页面)
    - 2.2. [行业详情页](#22-行业详情页)
    - 2.3. [公司历史交易数据页面](#23-公司历史交易数据页面)

# 股票数据爬取

## 1. 使用介绍
此爬虫程序的目的是从网络获取沪深a股行业板块中所有公司2017-2022年的股票交易数据。考虑到程序是io密集型，运用了多线程技术提高速度。但为了减少对网站服务器造成的影响和减少对本机内存的消耗，在程序中限制了每次只同时爬取10个公司的数据。
代码文件：pythoncode/get_shares_data.py
GetShareDate()为用户提供两个方法：
- getPlate()：返回行业板块中每个行业的名称与其行业内所有公司的name和code；
- getData(from_year, to_year, plates=None)：获取指定范围内的公司的股票数据，并写入文件中(data/行业名称/公司名.csv)，from_year开始年份，to_year结束年份，plates一个列表，每个元素是行业板块中的行业名称。

## 2. 网站分析

### 2.1. 行业板块页面
`http://quotes.money.163.com/old/#query=leadIndustry`
此页面展示了行业板块中的所有行业的信息，首先需要从这个页面中获得每个行业的id（plate_id），通过plate_id来构造出展示某行业下所有公司的页面的url。使用浏览器开发者工具分析得到api：
```
# http://quotes.money.163.com/hs/realtimedata/service/plate.php?
host=/hs/realtimedata/service/plate.php&page=0
&query=TYPE:HANGYE
&fields=RN,NAME,STOCK_COUNT,PE,LB,HSL,PERCENT,TURNOVER,VOLUME,PLATE_ID,TYPE_CODE,PRICE,UPNUM,DOWNNUM,MAXPERCENTSTOCK,MINPERCENTSTOCK
&sort=PERCENT
&order=desc
&count=47
&type=query
&callback=callback_1932607065
&req=51420
```
eg：只请求行业名称、id和所行公司数，`http://quotes.money.163.com/hs/realtimedata/service/plate.php?host=/hs/realtimedata/service/plate.php&page=0&query=TYPE:HANGYE&fields=NAME,PLATE_ID,STOCK_COUNT&sort=PERCENT&order=desc&count=47&type=query&callback=callback_1932607065&req=51420`

### 2.2. 行业详情页
家具制造行业详情页：http://quotes.money.163.com/old/#query=hy003008&DataType=HS_RANK&sort=PERCENT&order=desc&count=24&page=0 
此页面展示了家具制造行业下的所有公司信息。通过此页面，需要获得每个公司的code和name，api：
```
# http://quotes.money.163.com/hs/service/diyrank.php?
host=http%3A%2F%2Fquotes.money.163.com%2Fhs%2Fservice%2Fdiyrank.php
&page=0
&query=PLATE_IDS%3Ahy003008
&fields=NO%2CSYMBOL%2CNAME%2CPRICE%2CPERCENT%2CUPDOWN%2CFIVE_MINUTE%2COPEN%2CYESTCLOSE%2CHIGH%2CLOW%2CVOLUME%2CTURNOVER%2CHS%2CLB%2CWB%2CZF%2CPE%2CMCAP%2CTCAP%2CMFSUM%2CMFRATIO.MFRATIO2%2CMFRATIO.MFRATIO10%2CSNAME%2CCODE%2CANNOUNMT%2CUVSNEWS
&sort=PERCENT
&order=desc
&count=24
&type=query
```
- query：根据行业id查找
- field：需请求的字段
- page：指定页号
- count：每页展示的数据条数

### 2.3. 公司历史交易数据页面
http://quotes.money.163.com/trade/lsjysj_001323.html#01b07
通过前面获得的公司code构造请求url，返回的数据就在html页面中，通过BeautifuSoup模块提取。