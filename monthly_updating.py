import time
import sqlite3
import yfinance as yf

def updating(ticker):
    try:
        stock = yf.Ticker(ticker)

        info = stock.info
        history_daily = stock.history(period='1y', interval='1d')
        history_monthly = stock.history(period='20y', interval="1wk")

        with sqlite3.connect('permanent.db') as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO stock_details
                (ticker, company_name, sector, description)
                VALUES (?, ?, ?, ?)
                ''', (ticker, info.get('longName'), info.get('sector'), info.get('longBusinessSummary')))
            for date, row in history_daily.iterrows():
                cursor.execute('''
                INSERT OR REPLACE INTO price_history
                (ticker, history_date, close_price)
                VALUES (?, ?, ?)
                ''', (ticker, date.strftime('%Y-%m-%d'), row['Close']))

            for date, row in history_daily.iterrows():
                cursor.execute('''
                INSERT OR REPLACE INTO price_history_monthly
                (ticker, history_date, close_price)
                VALUES (?, ?, ?)
                ''', (ticker, date.strftime('%Y-%m-%d'), row['Close']))

    except Exception as e:
        print(f'ticker {ticker} skipped: error details: {e}')
        return False

    sleep_throttle = random.uniform(2.0, 4,5)
    time.sleep(sleep_throttle)
    return True
    
                
