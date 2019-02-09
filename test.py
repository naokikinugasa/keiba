import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import pprint
import csv
import pandas as pd
import numpy as np
import re

# driver = webdriver.Chrome("/Users/kinugasa/chromedriver_win32/chromedriver.exe")

# driver.get("https://db.netkeiba.com/?pid=race_top")

# a = driver.find_element_by_class_name("field")
# a.send_keys("園田")
# driver.find_element_by_class_name("form_side_btn").click()

# soup = BeautifulSoup(driver.page_source, "html.parser")

# tr_list = soup.find("tbody").find_all("tr")
# for tr in tr_list:
#     td = tr.find("td", class_="txt_l")
#     if td != None:
#         # print(td.find("a").get("href"))

# driver.close()
# TODO:レース数増やす

# def get_horse_url(race_url):

#     base_url = "https://db.netkeiba.com"

#     req = requests.get(race_url)
#     soup = BeautifulSoup(req.content, 'html.parser')
#     table1 = soup.find('table', attrs={'class':'race_table_01 nk_tb_common'})
#     table2 = soup.findAll('td', attrs={'class':'txt_l'})
#     horse_url_list = []
#     for a in table2:
#         b=a.find('a')
#         if b != None:
#             c=b.get('href')
#             if "horse" in c:
#                 horse_url_list.append(base_url + c)
#     return horse_url_list




def get_race_db():
    base_url = "http://www2.keiba.go.jp/KeibaWeb"
    race_list = []
    number_list = []
    result_list = []

    next_url = "http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2019%2f01%2f24&k_babaCode=27"
    for i in range(63):
        print(i)
        driver = webdriver.Chrome("/Users/kinugasa/chromedriver_win32/chromedriver.exe")
        driver.get(next_url)
        driver.find_element_by_class_name("yesterday").click()

        soup = BeautifulSoup(driver.page_source, "html.parser")

        tr_list = soup.find("section", class_="raceTable").find("table").find_all("tr", class_ = "data")

        for tr in tr_list:
            td_list = tr.find_all("td")
            url = tr.find("a")
            if url != None:
                url = url.get("href")[2:]
                race_list.append(base_url + url)
            number_list.append(td_list[8].string)
        for tr in tr_list:
            url = tr.find("a", string="成績")
            if url != None:
                url = url.get("href")[2:]
                result_list.append(base_url + url)
        next_url = str(driver.current_url)
        driver.quit()

    r = [race_list, number_list, result_list]
    l = [list(x) for x in zip(*r)]
    with open('data.csv', 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(l)

    return l


def get_result(race_url):
    req = requests.get(race_url)
    soup = BeautifulSoup(req.content, 'html.parser')
    dbtbl = soup.find("td", class_="dbtbl")
    horsecount = len(dbtbl.find_all("tr")) - 2
    data_list = [[0] * 3 for i in range(horsecount)]
    for i in range(horsecount):
        td_list = dbtbl.find_all("tr")[2 + i].find_all("td")
        result = td_list[0].string
        horsenum = td_list[2].string
        time = td_list[11].string.strip()
        data_list[i][0] = horsenum
        data_list[i][1] = result
        data_list[i][2] = time
    df = pd.DataFrame(data_list, columns=["horsenum", "result", "time_result"])
    return df


def get_horse_info(race_url, race_number):
    req = requests.get(race_url)
    soup = BeautifulSoup(req.content, 'html.parser')
    tborder = soup.find("tr", class_="tBorder")
    raceInfo = [[0] for i in range(race_number)]
    # TODO:rangeを馬数で動的に
    pastRace = [[0] for i in range(4)]
    IsCancell_list = [False] * 4
    
    tr_list = soup.find("section", class_="cardTable").find_all("tr")
    # 23456
    for h in range(race_number):
        td_list_2 = tr_list[2 + 5*h].find_all("td")
        if td_list_2[1].get("class") != None:
            if td_list_2[1].get("class")[0] == "horseNum":
                plus_horsenum_index = 0
        else:
            plus_horsenum_index = -1
        if td_list_2[2].find("a").get("class")[0] == "horseName":
            plus_index = 0
        else:
            plus_index = -1
        horsenum = td_list_2[1 + plus_horsenum_index].text
        horsename = td_list_2[2 + plus_index].text
        jockey = td_list_2[3 + plus_index].text.strip()
        raceInfo[h].append(horsenum)
        raceInfo[h].append(horsename)
        raceInfo[h].append(jockey)
        for i in range(0,4):
            l = td_list_2[5 + plus_index + i].text.split()
            # 過去走順位が取消かどうか
            if l != []:
                if l[0] == "取消":
                    IsCancell_list[i] = True
                else:
                    IsCancell_list[i] = False
            if IsCancell_list[i] == True or len(l) != 6:
                l = []
                for j in range(6):
                    l.append(None)
            pastRace[i].extend(l)
            # pastRace[i].extend(td_list_2[5 + i].text.split())

        td_list_3 = tr_list[3 + 5*h].find_all("td")
        trainer_weight = td_list_3[2].text
        #TODO:前走のレースURL。リンクないものがあるので一時コメントアウト
        # for i in range(0,4):
        #     print(td_list_3[3 + i])
        #     l = td_list_3[3 + i].find("a").get("href")
        #     if l == []:
        #         l.append("none")
        #     pastRace[i].append(l)
            # pastRace[i].append(td_list_3[3 + i].find("a").get("href"))
        
        td_list_4 = tr_list[4 + 5*h].find_all("td")
        father = td_list_4[0].text
        trainer = td_list_4[1].text
        w = td_list_4[2].text
        weight = w[:3]
        if weight == "－":
            weight = "cancel"
        dhweight = w[4:len(w)-1]
        if dhweight == "":
            dhweight = None
        raceInfo[h].append(weight)
        raceInfo[h].append(dhweight)
        for i in range(0,4):
            l = td_list_4[3 + i].text.split()
            if l == [] or IsCancell_list[i] == True or len(l) != 4:
                l = []
                for j in range(4):
                    l.append(None)
            pastRace[i].extend(l)
            # pastRace[i].extend(td_list_4[3 + i].text.split())
        td_list_5 = tr_list[5 + 5*h].find_all("td")
        mother = td_list_5[0].text
        for i in range(0,4):
            l = td_list_5[2 + i].text.split()
            if l == [] or IsCancell_list[i] == True or len(l) != 3:
                # l = []がなかったら取れた分だけはlに入っているので、超えてしまう
                l = []
                for j in range(3):
                    l.append(None)
            pastRace[i].extend(l)

            # pastRace[i].extend(td_list_5[2 + i].text.split())

        td_list_6 = tr_list[6 + 5*h].find_all("td")
        grandfather = td_list_6[0].text
        for i in range(0,4):
            l = td_list_6[3 + i].text.split()
            if l == [] or IsCancell_list[i] == True or len(l) != 2:
                l = []
                for j in range(2):
                    l.append(None)
            pastRace[i].extend(l)
        
        # [[],[]]→[]
        x = []
        for s in pastRace:
            x.extend(s)
        raceInfo[h].extend(x)
        pastRace = [[0] for i in range(4)]
        IsCancell_list = [False] * 4
    
    # pprint.pprint(raceInfo)
    # f = open('some.csv', 'w')
    # writer = csv.writer(f, lineterminator="\n")
    # writer.writerows(raceInfo)
    # f.close()
    idx = pd.MultiIndex.from_arrays(
        [['number','horsenum','horsename','jockey','weight','dhweight','past','past','past','past','past','past','past','past','past','past','past','past','past','past','past','past','past2','past2','past2','past2','past2','past2','past2','past2','past2','past2','past2','past2','past2','past2','past2','past2','past3','past3','past3','past3','past3','past3','past3','past3','past3','past3','past3','past3','past3','past3','past3','past3','past4','past4','past4','past4','past4','past4','past4','past4','past4','past4','past4','past4','past4','past4','past4','past4'],
        ['number','horsenum','horsename','jockey','weight','dhweight','0','rank','date','race_weight','place','m','number','popularity','weight','jockey','jockey_weight','time','0-0-0-0','3f','difference','1st','0','rank','date','race_weight','place','m','number','popularity','weight','jockey','jockey_weight','time','0-0-0-0','3f','difference','1st','0','rank','date','race_weight','place','m','number','popularity','weight','jockey','jockey_weight','time','0-0-0-0','3f','difference','1st','0','rank','date','race_weight','place','m','number','popularity','weight','jockey','jockey_weight','time','0-0-0-0','3f','difference','1st']
    ])
    df = pd.DataFrame(raceInfo)
    # if len(df.columns) > 70:
    #     for i in range(len(df.columns) - 70):
    #         df.drop([70 + i],axis=1, inplace=True)
    df.columns = idx
    # pd.set_option('display.max_columns', None)

    return df
    
    
def get_velocity(m, time):
    time_sec_list = []
    for t in list(time):
        if t == None:
            time_sec = 0
        else:
            base_time = pd.to_datetime('00:00.0', format='%M:%S.%f')
            time = pd.to_datetime(t,errors='coerce', format='%M:%S.%f') - base_time
            time_sec = time.total_seconds()
        time_sec_list.append(time_sec)
    # m = [float(mm[-4:]) if mm != None else 0 for mm in list(m)]
    # リスト内包表記で書きたい
    mmm = []
    for mm in list(m):
        if mm != None:
            if len(mm) == 5:
                mmm.append(float(mm[-4:]))
            else:
                mmm.append(float(mm[-3:]))
        else:
            mmm.append(0)
    velocity = np.array(mmm)/np.array(time_sec_list)
    return pd.Series(velocity)

def data_processing(df, result_url):
    # 出場取消馬の削除
    df = df[df.weight.weight != "cancel"]
    # TODO:データがないところを0で補完。タイムはその馬の平均値にしたい
    # df.fillna(0,inplace=True)
    
    print(result_url)

    velocity1 = get_velocity(df["past"]["m"], df["past"]["time"])
    velocity2 = get_velocity(df["past2"]["m"], df["past2"]["time"])
    velocity3 = get_velocity(df["past3"]["m"], df["past3"]["time"])
    velocity4 = get_velocity(df["past4"]["m"], df["past4"]["time"])
    new_data = df[['horsenum','horsename','weight','dhweight']]
    new_data.columns = ['horsenum', 'horsename','weight', 'dhweight']
    
    # new_data.dropna(subset=['weight'],inplace=True)
    
    new_data['velocity1'] = velocity1
    new_data['velocity2'] = velocity2
    new_data['velocity3'] = velocity3
    new_data['velocity4'] = velocity4

    mean = new_data[['velocity1','velocity2','velocity3','velocity4']].mean(axis=1)
    new_data['avg_velocity'] = mean
    new_data['weight'] = (new_data['weight'].astype(int) - new_data['weight'].astype(int).mean()) / new_data['weight'].astype(int).std()
    new_data['dhweight'] = (new_data['dhweight'].astype(int) - new_data['dhweight'].astype(int).mean()) / new_data['dhweight'].astype(int).std()
    pd.set_option('display.max_columns', None)
    n = new_data[['velocity1','velocity2','velocity3','velocity4','avg_velocity']]
    l = (n.astype(float) - n.mean()) / n.std()
    
    l['weight'] = new_data[['weight']]
    l['dhweight'] = new_data[['dhweight']]
    l['horsename'] = new_data[['horsename']]
    l['horsenum'] = new_data[['horsenum']]
    m = get_result(result_url)
    df = pd.merge(l, m, on="horsenum", how="inner")
    # TODO:上位３位を入れ替えではなく追加
    df.loc[df['result'].astype(int) <= 3, 'result'] = 1
    df.loc[df['result'].astype(int) > 3, 'result'] = 0
    df.fillna(df.median(),inplace=True)


    return df

def change_sort(mean_list):
    n = mean_list.pop(0)
    mean_list.append(n)
    return mean_list

# get_race_db()
df = pd.read_csv("data.csv", names=('race_url','horse_num','result_url'))

# df2 = get_horse_info("http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_raceDate=2019%2f01%2f18&k_raceNo=12&k_babaCode=27",12)
# df3 = data_processing(df2, "http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_raceDate=2019%2f01%2f18&k_raceNo=12&k_babaCode=27")
for i in range(47,100):
    print(i)
    if df.loc[i, 'race_url'] == "http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_raceDate=2019%2f01%2f23&k_raceNo=6&k_babaCode=27" or df.loc[i, 'race_url'] == "http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_raceDate=2019%2f01%2f17&k_raceNo=1&k_babaCode=27" or df.loc[i, 'race_url'] == "http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_raceDate=2019%2f01%2f16&k_raceNo=1&k_babaCode=27":
        print(df.loc[i, 'race_url'])
        continue
    df2 = get_horse_info(df.loc[i, 'race_url'],df.loc[i,'horse_num'])
    # print(df2)
    df3 = data_processing(df2, df.loc[i,'result_url'])
    # print(len(df3))
    if i == 0:
        df3.to_csv('data2.csv')
    else:
        df3.to_csv('data2.csv',mode="a",header=False)

# TODO:前走空の場合それ以前のデータもとれていない
#前走がどれくらい前か考慮していない
#get_race_db()で全部読み込んだ後にcsv出力している。1行ごとに書き込みたい(止まった時のために)
#出場取り消しの馬をmedianで埋めている。削除すべき。
#過去走の行が個数個入っているか確認。３個が２個しかない等を全部noneにしている。使えるデータは使いたい。
# 後ろから4個とっているため４桁mにしか対応できていない

