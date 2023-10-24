import os
import sqlite3


# 建立資料庫連線,若不存在,則新建資料庫
cur_path = os.path.dirname(__file__)  # 取得目前路徑，才能順利找到資料庫
conn = sqlite3.connect(
    cur_path + '/' + 'PM25.sqlite')  # 建立資料庫連線
cursor = conn.cursor()  # 建立 cursor物件

# 建立一個資料表(如果不存在)
sqlstr = '''
CREATE TABLE IF NOT EXISTS TablePM25 ("County" TEXT NOT NULL, "SiteName" TEXT NOT NULL,
"PM25" INTEGER, "Warning" TEXT NOT NULL, "DataCreationDate" TEXT NOT NULL
,"InsertNo" INTEGER NOT NULL )
'''
cursor.execute(sqlstr)

def fixInsertNum():
    insertNum = 12
    cursor = conn.execute("select * from TablePM25")
    rows = cursor.fetchall()
    for i in range(0,100):
        sql ='update TablePM25 set InsertNo = "'+str(insertNum)+'" where InsertNo = "'+str(insertNum+1)+'"'
        cursor = conn.execute(sql)
        insertNum += 1

fixInsertNum()
conn.commit()
conn.close()