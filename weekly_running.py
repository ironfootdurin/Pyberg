import yfinance as yf
import sqlite3
import pandas as pd

def get_sp500():
    with sqlite3.connect('S&P-500.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ticker FROM tickers')
        sp500 = cursor.fetchall()
        sp500 = [c[0] for c in sp500]
        return sp500

def setup_stocks():
    sp500 = get_sp500()
    prices = []
    data = yf.download(
        sp500,
        period='20d',
        group_by='ticker',
        progress=False,
        threads=True,
        )
    for symbol in sp500:
        #print(f'Getting ticker {symbol}')
        ticker = yf.Ticker(symbol)
        history = data[symbol]
        previous_price = history['Close'].iloc[-6]
        current_price = ticker.fast_info['last_price']
        change = (current_price - previous_price) / previous_price
        weight = abs(change)
        prices.append((symbol, change, weight))
        
    chosen_stocks = sorted(prices, key=lambda price: price[1], reverse=True)[:15]
    save_data(chosen_stocks)
    return True

def save_data(chosen_stocks):
    
    with sqlite3.connect('weekly_running.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recent_data (
                ticker TEXT PRIMARY KEY,
                change REAL,
                weight REAL
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

if __name__ == '__main__':
    setup_stocks()
        

    
