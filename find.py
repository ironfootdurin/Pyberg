# finds permanent company data

import sqlite3
import plotext as plt
import time
import threading
import update
from datetime import datetime
from rapidfuzz import fuzz, process, utils

def find(search):
    ticker_results = []
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        cursor.execute('select company_name, ticker from stock_details')
        names = cursor.fetchall()
    tickers = [name[1] for name in names]
    if len(search) <= 4:
        ticker_results = process.extract(search.upper(), tickers,  limit=8, score_cutoff=80)
    company_names = [name[0] for name in names]
    results = process.extract(search, company_names, processor=utils.default_process, limit=8)
    if ticker_results:
        return [ticker[0] for ticker in ticker_results]
    else:
        return [names[index][1] for match, score, index in results]



def recent_prices(ticker_code):
    with sqlite3.connect('obtaining_prices.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT price, last_updated FROM current_prices WHERE ticker = ? ', (ticker_code, ))
        result = cursor.fetchone()
        if result is None:
            cursor.execute("INSERT OR IGNORE INTO requests (ticker, status) VALUES (?, 'pending')", (ticker_code, ))
            conn.commit()
            return 0, True
        else:
            db_time = datetime.strptime(result[1], "%Y-%m-%d %H:%M:%S")
            current_time = datetime.utcnow()
            time_difference = current_time - db_time
            
            if time_difference.total_seconds() >= 1800:
                cursor.execute("INSERT OR IGNORE INTO requests (ticker, status) VALUES (?, 'pending')", (ticker_code, ))
                conn.commit()
                return result, True
            else:
                return result, False
                
            
            
def name(ticker_code):
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT company_name FROM stock_details WHERE ticker = ? ', (ticker_code, ))
        result = cursor.fetchone()

        if result is None:
            return None
        else:
            return result

def sector(ticker_code):
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT sector FROM stock_details WHERE ticker = ? ', (ticker_code, ))
        result = cursor.fetchone()

        if result is None:
            return None
        else:
            return result

def description(ticker_code):
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT description FROM stock_details WHERE ticker = ? ', (ticker_code, ))
        result = cursor.fetchone()

        if result is None:
            return None
        else:
            return result
        
def market_cap(ticker_code):
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT marketcap FROM company_marketcap WHERE ticker = ?',
            (ticker_code, )
        )
        result = cursor.fetchone()
        return result[0] if result else None


def monthly_data(ticker_code):
    import pandas as pd
    with sqlite3.connect('permanent.db') as conn:
        table = pd.read_sql_query('''SELECT * FROM price_history_monthly
                WHERE ticker = ?''', conn,  params = (ticker_code,))
        return table

    
def daily_data(ticker_code):
    import pandas as pd
    with sqlite3.connect('permanent.db') as conn:
        table = pd.read_sql_query('''SELECT * FROM price_history
                WHERE ticker = ?''', conn,  params = (ticker_code,))
        return table
    

def graph(table, ticker_code):
    
    result = name(ticker_code)
    plt.date_form('Y-m-d')

    plt.plot(table['history_date'], table['close_price'], label = ticker_code, marker = 'braille')

    plt.title(result[0])
    plt.xlabel('Date')
    plt.ylabel('Price ($)')
    plt.plotsize(240, 40)
    plt.grid(True, True)
    plt.theme('dark')
    
    plt.show()

def nicegui_graph(table, ticker_code):
    import pandas as pd
    result = name(ticker_code)
    title = result[0]
    chart_data = table[['history_date', 'close_price']].assign(
        history_date = table['history_date'].astype(str)
    ).values.tolist()
    configuration = {
        'backgroundColor': '#1A1A1A',
        'tooltip': {
            'trigger': 'axis',
            'backgroundColor': '#1A1A1A',
            'borderColor': '#181289',
            'borderWidth': 1,
            'textStyle': {'color': '#E0E0E0', 'fontFamily': 'sans-serif'},
            'axisPointer': {
                'type': 'line',
                'lineStyle': {'color': '#1D1A5D', 'type': 'dashed', 'width' : 1}, 
            }
        },
        'xAxis': {
            'type': 'time',
            'axisLine': {'lineStyle': {'color': '#1D1A5D'}},
            'splitLine': {'show': False}
            },
        'yAxis': {
            'type': 'value',
            'scale': True,
            'splitLine': {'lineStyle': {'color': '#1D1A5D'}}
            },
        'series': [{'type': 'line',
                    'smooth': 0.2,
                    'showSymbol': False,
                    'lineStyle': {'width': 2.5, 'color': '#00BFFF'},
                    'data': chart_data}]
        }
    return configuration
    

    
    

    


if __name__ == '__main__':

    ticker_code = input('Give ticker_code:')
    result = name(ticker_code)
    table = daily_data(ticker_code)
    print(table)
    graph(table, ticker_code)
    result = sector(ticker_code)
    print(result[0])
    result = description(ticker_code)
    print(result[0])




