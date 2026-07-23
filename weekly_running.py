import yfinance as yf
import sqlite3
import pandas as pd
import time
from datetime import timedelta


def get_sp500():
    with sqlite3.connect('S&P-500.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ticker FROM tickers')
        sp500 = cursor.fetchall()
        sp500 = [c[0] for c in sp500]
        return sp500

def online_run():
    sp500 = get_sp500()
    prices = []
    total_weight = 0
    data = yf.download(
        sp500,
        period='20d',
        interval='1wk', 
        group_by='ticker',
        progress=True,
        threads=True,
        )
    print(data)
    for i, symbol in enumerate(sp500):
        try:
            print(f'Getting ticker {symbol}: ticker {i}/{len(sp500)}'.ljust(50), end='\r', flush=True)
            #print(f'Getting ticker {symbol}: ticker {i}/{len(sp500)}')
            ticker = yf.Ticker(symbol)
            history = data[symbol]
            previous_price = history['Close'].iloc[-2]
            
            current_price = ticker.fast_info['last_price']
            change = (current_price - previous_price) / previous_price
            weight = abs(change)
            prices.append((symbol, change, weight, current_price))
        except Exception as e:
            print(e)
    chosen_stocks = sorted(prices, key=lambda price: price[1])[:32]
    save_data(chosen_stocks)
    total_weight = sum(item[2] for item in chosen_stocks)
    return chosen_stocks, total_weight

def save_data(chosen_stocks):
    
    with sqlite3.connect('weekly_running.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recent_data (
                ticker TEXT PRIMARY KEY,
                change REAL,
                weight REAL,
                price REAL
                )
            ''')
        for stocks in chosen_stocks:
            cursor.execute('INSERT OR REPLACE INTO recent_data (ticker, change, weight ) VALUES (?, ?, ?)', (stocks[0], stocks[1], stocks[2]))
        conn.commit()

def retrieve_data():
    with sqlite3.connect('weekly_running.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ticker, change, weight FROM recent_data')
        data = cursor.fetchall()
        return data
    
def offline_run():
    with sqlite3.connect('weekly_running.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ticker, change, weight, price FROM recent_data')
        data = cursor.fetchall()
    total_weight = sum(item[2] for item in chosen_stocks)
    return chosen_stocks, total_weight
    
    

if __name__ == '__main__':
    start = time.time()
    stocks, total_weight = online_run()
    end = time.time()
    h, r = divmod(end-start, 3600)
    m, s = divmod(r, 60)
    print(f'Operation took {h} hours {m} minutes and {s} seconds')
    input('Press enter to exit')
        
        

