#getting and saving the list of s&p 500 companies
import sqlite3
import pandas as pd
import requests
import io
import find
import updating as create

def save(ticker):
    with sqlite3.connect('S&P-500.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO tickers (ticker) VALUES (?)', (ticker, ))



if __name__ == '__main__':

    n = 0
    
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    with sqlite3.connect('S&P-500.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickers (
                ticker TEXT PRIMARY KEY
                )
            ''')

    response = requests.get(url, headers=headers)

    tables = pd.read_html(io.StringIO(response.text))

    sp500 = tables[0]['Symbol'].tolist()

    sp500 = [company.replace('.', '-') for company in sp500]

    for ticker in sp500:
        n += 1
        print(f'Running {ticker}')
        result = create.updating(ticker)
        if result:
            print(f' {n}/500: Success!')
        else:
            print('Failed')
