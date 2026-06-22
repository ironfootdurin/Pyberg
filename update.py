#find current company cost
import sqlite3
import time
import random
import yfinance as yf


def update_table():
    with sqlite3.connect('obtaining_prices.db', timeout=20) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS current_prices (
                ticker TEXT PRIMARY KEY, 
                price REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                ticker TEXT PRIMARY KEY, 
                status TEXT
                )
            ''')
        conn.commit()
        

    while True:
        tickers_updating = []
        with sqlite3.connect('obtaining_prices.db', timeout=20) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ticker FROM requests WHERE status = 'pending'")
            tickers_to_update = cursor.fetchall()
            tickers_updating = list(tickers_to_update)
        if tickers_updating:
            for ticker in tickers_updating:
                ticker = ticker[0]
                try:
                    stock = yf.Ticker(ticker)
                    price = stock.fast_info['last_price']
                    with sqlite3.connect('obtaining_prices.db', timeout=20) as conn:
                            cursor = conn.cursor()
                            cursor.execute('''INSERT OR REPLACE
                             INTO current_prices (ticker, price, last_updated)
                             VALUES (?, ?, CURRENT_TIMESTAMP)''', (ticker, price))
                            cursor.execute("DELETE FROM requests WHERE ticker = ?", (ticker, ))
                            conn.commit()
                    time.sleep(random.uniform(0.2, 0.5))
                except Exception as e:
                    print(f'The ticker {ticker} is not valid. Moving on.')
                    with sqlite3.connect('obtaining_prices.db', timeout=20) as conn:
                        cursor.execute("DELETE FROM requests WHERE ticker = ?", (ticker, ))
                        conn.commit()
                    time.sleep(random.uniform(0.2, 0.5))
            time.sleep(random.uniform(1.5, 3.5))
        else:
            time.sleep(0.25)


            


        
        
