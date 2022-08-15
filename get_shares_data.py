import time
import requests
import json
import re
import threading
from bs4 import BeautifulSoup
import pandas as pd
import os


class GetSharesData():
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.patter = re.compile(r"[`~!@#$%^&*()\-+=<>?:\"{}|,\/;'\\[\]·~！@#￥%……&*（）——\-+={}|《》？：“”【】、；‘'，。、]")
        self.header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
    def getData(self, from_year, to_year, plates:iter=None):
        self.from_year = from_year
        self.to_year = to_year
        self.plates=plates
        if not hasattr(self, 'plate_dict'):
            self.get_ccode()
        self.task_plate()
        self.get_shares_data()
        # self.ccode_in_one_plate('http://quotes.money.163.com/hs/service/diyrank.php?host=http%3A%2F%2Fquotes.money.163.com%2Fhs%2Fservice%2Fdiyrank.php&page=0&query=PLATE_IDS%3Ahy003008&fields=CODE&sort=PERCENT&order=desc&count=31&type=query')
    
    # 得到板块信息
    def getPlate(self):
        if not hasattr(self, 'plate_dict'):
            self.get_ccode()
        plate_lst = []
        for plate_name, company_lst in self.plate_dict.items():
            plate_lst.append((plate_name, len(company_lst)))
        return plate_lst
    # 发送请求
    @staticmethod
    def send_req(url, headers=None):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        
        
    # 构造某个板块详细信息的网页的url
    @staticmethod
    def plate_url(plate_id, count):
        return f' http://quotes.money.163.com/hs/service/diyrank.php?host=http%3A%2F%2Fquotes.money.163.com%2Fhs%2Fservice%2Fdiyrank.php&page=0&query=PLATE_IDS%3A{plate_id}&fields=CODE,NAME&sort=PERCENT&order=desc&count={count}&type=query'
    
    
    # 得到一个板块下的所有公司的code
    def ccode_in_one_plate(self, name, plate_url):
        response = self.send_req(plate_url,headers=self.header)
        if response:
            code_lst = []
            for c in response.json().get("list"):
                code_lst.append((c.get("CODE"), c.get("NAME")))
            self.plate_dict[name]=code_lst   
            
            
    # 得到每个板块下的所有公司的code
    def get_ccode(self):
        # 第一步，获取每个板块的id（plate_id），构造出板块详细页面的url
        plate_api_prefix = 'http://quotes.money.163.com/hs/realtimedata/service/plate.php?'
        query_args = [
            'host=/hs/realtimedata/service/plate.php&page=0',
            'query=TYPE:HANGYE',
            'fields=PLATE_ID,STOCK_COUNT,NAME',
            'sort=PERCENT',
            'order=desc',
            'count=47',
            'type=query',
            'callback=callback_1932607065',
            'req=51420'
        ]
        plate_api = plate_api_prefix + '&'.join(query_args)
        response = self.send_req(plate_api,headers=self.header)
        raw_json_data = re.search(r"(?<=callback_1932607065\().*(?=\))", response.text).group()
        json_data = json.loads(raw_json_data)
        self.plate_dict = {}
        for i in json_data.get('list'):
            plate_id = i.get("PLATE_ID")
            stock_count = i.get("STOCK_COUNT")
            name = i.get("NAME")
            self.plate_dict[name] = self.plate_url(plate_id, stock_count)
        # 第二步，获取每个板块中所有公司的code
        t_lst = []
        for plate_name, plate_url in self.plate_dict.items():
            t = threading.Thread(target=self.ccode_in_one_plate, args=(plate_name, plate_url))
            t_lst.append(t)
            t.start()
        for t in t_lst:
            t.join()
        print('公司code获取完毕...')
    # 提取出用户需要爬取的板块
    def task_plate(self):
        self.task_plate_dict = {}
        if self.plates:
            for plate_name, company_lst in self.plate_dict.items():
                if plate_name in self.plates:
                    self.task_plate_dict[plate_name]=company_lst
        else:
            self.task_plate_dict = self.plate_dict
    # 请求一个公司一个季度的数据
    def req_data(self, url, code, company_name, plate_name,cname):
        response = self.send_req(url,headers=self.header)
        if not response:
            return None
        response.encoding = 'utf8'
        soup = BeautifulSoup(response.text, "lxml")
        if soup:
            # 提取数据，判断是否为空，如果为空就返回None
            tr_lst= soup.select(r'.border_box tr')
            if not tr_lst:
                return None
            # 得到标题栏
            th_lst = soup.select(r'.border_box th')
            t_head = []
            for th in th_lst:
                t_head.append(th.string)
            t_head.insert(1, '公司名')
            t_head.insert(2, '公司code')
            df_dict = {key:[] for key in t_head}
            df = pd.DataFrame({key:[] for key in t_head})
            # 获取内容
            for tr in tr_lst:
                td_lst = tr.select('td')
                line = []
                for td in td_lst:
                    line.append(td.string)
                if line:
                    # y,m,d = time.strptime(line[0], "%Y-%m-%d")[:3]
                    # line[0] = datetime.datetime(y,m,d)
                    line.insert(1, company_name)
                    line.insert(2, code)
                    line = [str(i) for i in line]
                    for i,j in zip(df_dict, line):
                        df_dict[i].append(j)
            df = pd.DataFrame(df_dict)
            with self.lock:
                if not os.path.exists(f'data/{plate_name}'):
                    os.makedirs(f'data/{plate_name}')
                if not os.path.exists(f'data/{plate_name}/{cname}.csv'):
                    df.to_csv(f'data/{plate_name}/{cname}.csv', mode='a',index = False)
                else:
                    df.to_csv(f'data/{plate_name}/{cname}.csv', mode='a', header=None,index = False)
            del df

        
    # 获取一个公司的所有股票信息
    def sdata_in_onec(self, code, company_name, plate_name):
        cname = re.sub(self.patter, '', company_name)
        print(f'\t{company_name}...')
        t_lst = []
        for year in range(self.from_year, self.to_year+1):
            for season in range(1, 5):
                url = f'http://quotes.money.163.com/trade/lsjysj_{code[1:]}.html?year={year}&season={season}'
                # self.req_data(url, code, company_name, plate_name)
                t = threading.Thread(target=self.req_data, args=(url, code, company_name, plate_name, cname))
                t_lst.append(t)
                t.start()
            for t in t_lst:
                t.join()
        print(f'\t{company_name}完毕')

    
    # 获取所有公司的股票信息
    def get_shares_data(self):
        t_lst = []
        t_count = 0
        for plate_name, company_lst in self.task_plate_dict.items():
            print(f"板块: {plate_name}")
            for company in company_lst:
                cname = re.sub(self.patter, '', company[1])
                if os.path.exists(f"data/{plate_name}/{cname}.csv"):
                    continue
                t = threading.Thread(target=self.sdata_in_onec, args=(company[0], company[1], plate_name))
                t_lst.append(t)
                t.start()
                t_count+=1
                if t_count >= 10:
                    for t in t_lst:
                        t.join()
                    t_count = 0
                    t_lst=[]
            print(f"{plate_name}完毕...")
        
        
g = GetSharesData()
g.getData(2017, 2022)
# plates = g.getPlate()
# for plate in plates:
#     print(plate)

# 难点：怎么接着上次继续爬取；数据量大怎么处理才能少消耗内存;多线程写文件时怎么保证数据准确