import sqlite3
import pickle

import datetime as datetime

old_con = sqlite3.connect('../historic_klines.db')
old_cur = old_con.cursor()

new_con = sqlite3.connect('../tmp/cache.db')
new_cur = new_con.cursor()

new_cur.execute(f"drop table if exists prices")
new_cur.execute(f"create table prices (symbol text, time timestamp, price integer)")

old_rows = old_cur.execute(f"select * from 'unnamed'")
i = 0
for old_row in old_rows:
    symbol, ts_str = old_row[0].split(" - ")
    ts = datetime.datetime.strptime(ts_str, "%d %b %Y %H:%M:%S")
    price = pickle.loads(bytes(old_row[1]))
    new_cur.execute(f"insert into prices values(?, ?, ?)", (symbol, ts, price))
    i += 1
    if i % 1000 == 0:
        print(f"Imported {i}")

old_con.commit()
old_con.close()

new_con.commit()
new_con.close()
