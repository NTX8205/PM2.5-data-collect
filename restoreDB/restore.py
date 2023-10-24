import os
import sqlite3

cur_path = os.path.dirname(__file__)  # 取得目前路徑，才能順利找到資料庫
conn = sqlite3.connect(
    cur_path + '/' + 'PM25.sqlite')  # 建立資料庫連線
backupdb = sqlite3.connect(cur_path + '/' + 'backup.sqlite')
backupdb.backup(conn)
