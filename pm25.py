import io
import os
import sqlite3
import hashlib
from bs4 import BeautifulSoup
import json
import time
import requests
import datetime

# 建立資料庫連線,若不存在,則新建資料庫
cur_path = os.path.dirname(__file__)  # 取得目前路徑，才能順利找到資料庫
conn = sqlite3.connect(cur_path + "/" + "PM25.sqlite")  # 建立資料庫連線
cursor = conn.cursor()  # 建立 cursor物件

# 建立一個資料表(如果不存在)
sqlstr = """
CREATE TABLE IF NOT EXISTS TablePM25 ("County" TEXT NOT NULL, "SiteName" TEXT NOT NULL,
"PM25" INTEGER, "Warning" TEXT NOT NULL, "DataCreationDate" TEXT NOT NULL
,"InsertNo" INTEGER NOT NULL )
"""
cursor.execute(sqlstr)

with open("setting.json", "r", encoding="utf8") as jfile:
    jdata = json.load(jfile)


# 細浮微粒資料(PM2.5) : 資料集代碼 aqx_p_02
url = "https://data.epa.gov.tw/api/v2/aqx_p_02?api_key=" + jdata["api"] + "&format=json"


def getPM25Data(url):
    while True:
        try:
            html = requests.get(url).text
            if html == "請勿頻繁索取資料, 一分鐘呼叫API的次數不可大於1次":
                time.sleep(60)
            else:
                return html
        except:
            print("Connection refused by the server.")
            print("Let me sleep for 5 seconds")
            print("ZZzzzz")
            time.sleep(5)
        print("Was a nice sleep, now let me continue")


# 讀取網頁原始碼
html = getPM25Data(url)  # .encode('utf-8')

html = html.encode("utf-8")
# 判斷網頁是否更新
new_md5 = hashlib.md5(html).hexdigest()
old_md5 = ""
if os.path.exists("old_md5.txt"):
    with open("old_md5.txt", "r") as f:
        old_md5 = f.read()
with open("old_md5.txt", "w+") as f:
    f.write(new_md5)

###########################
# 立即測試用,強設資料已更新
# old_md5 = ""
###########################


def PM25Warning(num):
    if num < 36:
        return "綠"
    elif num < 54:
        return "黃"
    elif num < 71:
        return "紅"
    elif num >= 71:
        return "紫"


def showAllData():
    n = 1
    insertNum = getCurrentInsertNum()
    print("============= 全國最新PM2.5資訊 =============")
    cursor = conn.execute(
        "select * from TablePM25 where InsertNo=" + '"' + str(insertNum) + '"'
    )
    rows = cursor.fetchall()
    for row in rows:
        print(
            n,
            "站名:" + row[1] + "(" + row[0] + ")",
            "PM2.5=" + str(row[2]),
            "Date=" + row[4],
        )
        n += 1


def showSelectData(county, times):
    findDate = conn.execute(
        "select distinct DataCreationDate from TablePM25 order by DataCreationDate desc limit "
        + str(times)
    )
    dates = findDate.fetchall()
    dateList = []
    for date in dates:
        dateList.append(date)

    for i in dateList:
        strdate = "".join(i)
        cursor = conn.execute(
            "select * from TablePM25 where County= "
            + '"'
            + county
            + '"'
            + "and DataCreationDate="
            + '"'
            + strdate
            + '"'
        )
        rows = cursor.fetchall()
        print(
            "================== "
            + county
            + "["
            + strdate
            + "]"
            + " ====================="
        )
        for row in rows:
            print("站名:" + row[1], "PM2.5=" + str(row[2]), "*** " + row[3] + " ***")


def getCurrentInsertNum():
    cursor = conn.execute("select max(InsertNo) from TablePM25")
    rows = cursor.fetchone()
    if rows[0] is None:
        return 0
    else:
        return rows[0]


if new_md5 != old_md5:
    insertNum = getCurrentInsertNum()
    print("資料已更新...")
    print("*** currentInsertNo = " + str(insertNum))
    sp = BeautifulSoup(html, "html.parser")
    # 將網頁內客轉換成JSON资料:dict
    jsondata = json.loads(sp.text)
    # 擷取JSON資料中監測站的PM2.5資料:list of dict
    sitesList = jsondata["records"]

    for site in sitesList:
        SiteName = site["site"]
        County = site["county"]
        PM25 = 0 if site["pm25"] == "" else int(site["pm25"])
        warning = PM25Warning(PM25)
        currentDate = site["datacreationdate"]
        # 新增一筆記錄
        sqlstr = "insert into TablePM25 values('{}','{}', {}, '{}', '{}', {})".format(
            County, SiteName, PM25, warning, currentDate, insertNum + 1
        )
        cursor.execute(sqlstr)
    conn.commit()  # 主動更新
    showAllData()
    city = "臺中市"
    showSelectData(city, 3)
else:
    print("資料未更新,從資料庫讀取...")
    insertNum = getCurrentInsertNum()
    print("*** currentInsertNo = " + str(insertNum))
    showAllData()
    city = "臺中市"
    showSelectData(city, 3)


# print log
with open("recent.log", "a+") as f:
    loc_dt = datetime.datetime.today()
    loc_dt_format = loc_dt.strftime("%Y/%m/%d %H:%M:%S")
    if new_md5 != old_md5:
        f.write(str(loc_dt_format) + " success read and add new data\n")
        print("\ncomplete add data, 5 seconds will exit!")
    else:
        f.write(str(loc_dt_format) + " success read\n")
        print("\ncomplete read data and nothing add, 5 seconds will exit!")

# backup database and sql
backupdb = sqlite3.connect(cur_path + "/" + "backup.sqlite")
conn.backup(backupdb)

with io.open("backup.sql", "w+", encoding="utf8") as backup:
    # iterdump() function
    for line in conn.iterdump():
        backup.write("%s\n" % line)

print("\nBackup performed successfully!")
print("Data Saved as backup.sql")
conn.close()  # 關閉資料庫連線
backupdb.close()
time.sleep(2)
