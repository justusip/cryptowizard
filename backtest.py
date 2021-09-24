import sqlite3

import datetime as datetime

con = sqlite3.connect('cache/cache.db')
cur = con.cursor()

rows = cur.execute(f"select * from 'prices' where symbol='ADAUSDT' order by symbol asc, time asc")
start = datetime.datetime(2021, 8, 1)
end = datetime.datetime(2021, 9, 1)

print(f"Starting at {start} and ending at {end}.")

i = 0
for row in rows:
    print(row)

con.close()
