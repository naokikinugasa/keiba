import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import pprint
import csv
import pandas as pd
import numpy as np
import re
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
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




def get_race_url_list(start_url, end_url, to_csv, Is_predict):
    base_url = "http://www2.keiba.go.jp/KeibaWeb"
    race_list = []
    number_list = []
    result_list = []

    next_url = end_url
    while next_url != start_url:
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
            if Is_predict == False:
                url = tr.find("a", string="成績")
                if url != None:
                    url = url.get("href")[2:]
                    result_list.append(base_url + url)
            else:
                result_list.append("url")
        next_url = str(driver.current_url)
        driver.quit()

    r = [race_list, number_list, result_list]
    l = [list(x) for x in zip(*r)]
    with open(to_csv, 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(l)

    return l


def get_result(race_url):
    req = requests.get(race_url)
    soup = BeautifulSoup(req.content, 'html.parser')
    dbtbl = soup.find_all("td", class_="dbtbl")
    horsecount = len(dbtbl[0].find_all("tr")) - 2
    data_list = [[0] * 3 for i in range(horsecount)]
    for i in range(horsecount):
        td_list = dbtbl[0].find_all("tr")[2 + i].find_all("td")
        result = td_list[0].string
        # TODO:数字以外除外しているが数字以外は0が入っている
        if result.isdigit():
            horsenum = td_list[2].string
            time = td_list[11].string.strip()
            data_list[i][0] = horsenum
            data_list[i][1] = result
            data_list[i][2] = time
    df = pd.DataFrame(data_list, columns=["horsenum", "result", "time_result"])
    
    # 払戻金
    l = dbtbl[1].find("tr", class_="dbdata")
    td_list = l.find_all("td")
    horsenum_r = [i.strip() for i in list(td_list[4].strings)]
    multipul_wins = [int(i.strip().strip("円").replace(",","")) for i in list(td_list[5].strings)]
    df2 = pd.DataFrame([horsenum_r, multipul_wins]).T
    df2.columns = ["horsenum", "multipul_wins"]
    df = pd.merge(df, df2, on="horsenum", how="outer")
    df.fillna({"multipul_wins": 0}, inplace=True)
    return df
# print(get_result("http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_raceDate=2019%2f01%2f24&k_raceNo=11&k_babaCode=27"))
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
        if weight == "－" or weight == "計不":
            weight = "cancel"
        dhweight = w[4:len(w)-1]
        if dhweight == "":
            dhweight = 0
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

def data_processing(df):
    # 出場取消馬の削除
    df = df[df.weight.weight != "cancel"]
    # TODO:データがないところを0で補完。タイムはその馬の平均値にしたい
    # df.fillna(0,inplace=True)
    
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
    # m = get_result(result_url)
    # df = pd.merge(l, m, on="horsenum", how="inner")
    # # TODO:上位３位を入れ替えではなく追加
    # df.loc[df['result'].astype(int) <= 3, 'result'] = 1
    # df.loc[df['result'].astype(int) > 3, 'result'] = 0
    # df.fillna(df.median(),inplace=True)


    return l

def merge_info_and_result(info_df, result_url):
    m = get_result(result_url)
    df = pd.merge(info_df, m, on="horsenum", how="inner")
    # TODO:上位３位を入れ替えではなく追加
    df.loc[df['result'].astype(int) <= 3, 'result'] = 1
    df.loc[df['result'].astype(int) > 3, 'result'] = 0
    df.fillna(df.median(),inplace=True)
    return df


def to_csv(url_list_csv, to_csv,Is_predict):
    df = pd.read_csv(url_list_csv, names=('race_url','horse_num','result_url'))

    # df2 = get_horse_info("http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_raceDate=2019%2f01%2f18&k_raceNo=12&k_babaCode=27",12)
    # df3 = data_processing(df2, "http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_raceDate=2019%2f01%2f18&k_raceNo=12&k_babaCode=27")
    for i in range(0,10):
        # if i == 66 or i == 105 or i == 139 or i == 146 or i == 151 or i == 163 or i == 169 or i == 173:
        #     continue
        print(i)
        df2 = get_horse_info(df.loc[i, 'race_url'],df.loc[i,'horse_num'])
        # print(df2)
        df3 = data_processing(df2)
        if Is_predict == False:
            df3 = merge_info_and_result(df3, df.loc[i,'result_url'])
        # print(len(df3))
        if i == 0:
            df3.to_csv(to_csv)
        else:
            df3.to_csv(to_csv,mode="a",header=False)
# get_race_url_list("http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2019%2f02%2f07&k_babaCode=27", "http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2019%2f02%2f12&k_babaCode=27", "test.csv", False)
# to_csv('data_1_31.csv', '1_31.csv',True)

from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import precision_score, recall_score, accuracy_score
from imblearn.under_sampling import RandomUnderSampler

#TODO:引数をrace_urlだけにしたい
def predict(race_url, horse_num):
    race_df = get_horse_info(race_url,horse_num)
    race_df = data_processing(race_df)
    # 結果がある場合、精度確認の場合
    race_df = merge_info_and_result(race_df, "http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_raceDate=2019%2f02%2f11&k_raceNo=1&k_babaCode=27")

    df = pd.read_csv("1_30.csv")
    df = df.dropna(how="any")
    train_X = df
    train_y = df.result
    race_df.dropna(how="any", inplace=True)
    test_X = race_df.reset_index(drop=True)
    test_y = test_X.result

    sampler = RandomUnderSampler(ratio={0:train_X['result'].sum(), 1:train_X['result'].sum()}, random_state=42)
    train_X, train_y = sampler.fit_resample(train_X, train_y)
    train_X = pd.DataFrame(train_X)
    Is_predict = True
    train_X.columns = ["num","velocity1","velocity2","velocity3","velocity4","avg_velocity","weight","dhweight","horsename","horsenum","result","time_result","multipul_wins"]
    
    knn = KNeighborsClassifier(n_neighbors=30) # インスタンス生成。
    knn.fit(train_X.loc[:,'velocity1':'dhweight'], train_y) 
    pred_y = knn.predict(test_X.loc[:,'velocity1':'dhweight'])
    # print(precision_recall_fscore_support(test_y, pred_y))
    
    df3 = pd.concat([test_X['horsename'],  pd.DataFrame(pred_y)], axis=1,)
    df3.columns = ['horsename', 'predict']
    pd.set_option('display.max_rows', None)
    print(df3)
    sales  = (pred_y * test_X.multipul_wins).sum()
    cost = pred_y.sum() * 100
    profits = sales - cost
    recovery_rate = sales/cost
    print(sales, cost, profits, recovery_rate)


##k-NNのパラメータ比較
def show_n_neighbors(data_csv):
    df = pd.read_csv(data_csv)
    df = df.dropna(how="any")
    train_X, test_X, train_y, test_y = train_test_split(
        df.loc[:,'velocity1':'dhweight'], df.result, test_size=0.2)
    accuracy = []
    k_range = np.arange(1,100)
    for k in k_range:
        knn = KNeighborsClassifier(n_neighbors=k) # インスタンス生成。
        knn.fit(train_X, train_y)                 # モデル作成実行
        pred_y = knn.predict(test_X)              # 予測実行
        accuracy.append(accuracy_score(test_y, pred_y)) # 精度格納
    plt.plot(k_range, accuracy)
    plt.show()

##ランダムフォレストのパラメータ比較
def show_n_estimators(data_csv):
    df = pd.read_csv(data_csv)
    df = df.dropna(how="any")
    train_X, test_X, train_y, test_y = train_test_split(
        df.loc[:,'velocity1':'dhweight'], df.result, test_size=0.2)
    accuracy = []
    n_estimators = np.arange(1,50)
    for n in n_estimators:
        model =  RandomForestClassifier(n_estimators=n, random_state=42)
        model.fit(train_X, train_y)                 # モデル作成実行
        pred_y = model.predict(test_X)              # 予測実行
        accuracy.append(accuracy_score(test_y, pred_y)) # 精度格納
    plt.plot(n_estimators, accuracy)
    plt.show()

def evaluate(data_csv):
    df = pd.read_csv(data_csv)
    df = df.dropna(how="any")
    train_X, test_X, train_y, test_y = train_test_split(
        df, df.result, test_size=0.2)
    train_X = train_X.loc[:,'velocity1':'dhweight']
    knn = RandomForestClassifier(n_estimators=10, random_state=42) # インスタンス生成。
    knn.fit(train_X, train_y)                 # モデル作成実行
    pred_y = knn.predict(test_X.loc[:,'velocity1':'dhweight'])
    sales  = (pred_y * test_X.multipul_wins).sum()
    cost = pred_y.sum() * 100
    profits = sales - cost
    recovery_rate = sales/cost
    print(sales, cost, profits, recovery_rate)
    
evaluate('1_30.csv')
# predict("http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_raceDate=2019%2f02%2f11&k_raceNo=1&k_babaCode=27", 10)


# TODO:前走空の場合それ以前のデータもとれていない
#前走がどれくらい前か考慮していない
#get_race_url_list()で全部読み込んだ後にcsv出力している。1行ごとに書き込みたい(止まった時のために)
#出場取り消しの馬をmedianで埋めている。削除すべき。
#過去走の行が個数個入っているか確認。３個が２個しかない等を全部noneにしている。使えるデータは使いたい。
# 後ろから4個とっているため４桁mにしか対応できていない
# get_race_url_list()のend_urlの1つ前までしかとれない仕様になっている