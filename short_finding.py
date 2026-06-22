import sqlite3
import pandas as pd
import time
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt

start = time.time()




#plan:
#Take all s&p companies
#take worst 20
#invest in them until next week


def get_sp500():
    with sqlite3.connect('S&P-500.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ticker FROM tickers')
        sp500 = cursor.fetchall()
        sp500 = [c[0] for c in sp500]
        return sp500

def get_sp_data(sp):
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(sp))
        
        cursor.execute(f'''
            SELECT ticker, close_price, history_date
            FROM price_history_monthly
            WHERE ticker IN ({placeholders})
            ''', sp)
        items = cursor.fetchall()
        print(len(items))
        print('done')

def sp_starting_dates():
    with sqlite3.connect('S&P-500.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ticker, start_date
            FROM join_500_dates
        """)
        ticker_dates = dict(cursor.fetchall())
        return ticker_dates

#Seperating into weekly data info for each stock:
def restore_data(sp, ticker_dates):
    
    tables = []
    with sqlite3.connect('permanent.db') as conn:
        
        for ticker in sp:        
            table = pd.read_sql_query(f'''
                SELECT ticker, close_price, history_date
                FROM price_history_monthly
                WHERE ticker = ?''', conn, params=(ticker, ))

            company_start = ticker_dates.get(ticker)
            if company_start is None:
                continue

            table = table[table['history_date'] >= company_start]
            tables.append(table)

        all_data = pd.concat(tables, ignore_index=True)

    with sqlite3.connect('S&P-500.db') as conn:
        cursor = conn.cursor()
        all_data.to_sql('weekly',
                conn,
                if_exists='replace',
                index=False
                      )

def get_dates():
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        df = pd.read_sql_query('''
                SELECT ticker, close_price, history_date
                FROM price_history_monthly
                WHERE ticker = "SPY"''', conn)
        df['history_date'] = pd.to_datetime(df['history_date'], format='%Y-%m-%d')
        df = df.set_index('history_date')
        return pd.Series(df.index)

def benchmark():
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        df = pd.read_sql_query('''
                SELECT ticker, close_price, history_date
                FROM price_history_monthly
                WHERE ticker = "SPY"''', conn)
        df['history_date'] = pd.to_datetime(df['history_date'], format='%Y-%m-%d')
        df = df.set_index('history_date')
        return df

    
def load_sp_500_data():
    with sqlite3.connect('S&P-500.db') as conn:
        cursor = conn.cursor()
        df = pd.read_sql_query(f'''
                SELECT ticker, close_price, history_date
                FROM weekly''', conn)
        df['history_date'] = pd.to_datetime(df['history_date'], format='%Y-%m-%d')
        df = df.set_index('history_date')
        return df

def time_machine(df, dates, n):
    tables = []
    for i, date in enumerate(dates):
        
        if i == 0 or i + n >= len(dates):
            continue
        current_date = dates.iloc[i]
        current_info = df[df.index == current_date]
        
        prev_date = dates.iloc[i-1]
        prev_info = df[df.index == prev_date]
        
        next_date = dates.iloc[i+n]
        next_info = df[df.index == next_date]

        tables.append((current_info, prev_info, next_info))

    return tables
        
def choose(merged, n):
        chosen = merged.sort_values('performance', ascending=False).iloc[n]
        return chosen
    

def test_time(tables, n, weight, df):
    start1 = time.time()
    ttl_margins = []
    margins = []
    changes = []
    benchmark_changes = []
    for date in tables:
        date1 = date[0].index[0]
        date2 = date[2].index[0]
        merged = pd.merge(date[0], date[1], on='ticker', suffixes=('_old', '_new'))
        merged['performance'] = (merged['close_price_new'] - merged['close_price_old']) / merged['close_price_old'] * 100    

        if n >= len(merged):
            continue
        chosen = choose(merged, n)

        buying_price = date[0][date[0]['ticker'] == chosen['ticker']]['close_price'].iloc[0]

        result = date[2][date[2]['ticker'] == chosen['ticker']]['close_price'].iloc[0]

        change = (result - buying_price) / buying_price * 100

        dated_benchmark_start = df[df.index == date1]
        dated_benchmark_end = df[df.index == date2]
        
        benchmark_start_price = dated_benchmark_start['close_price'].iloc[0]
        benchmark_end_price = dated_benchmark_end['close_price'].iloc[0]

        benchmark_change = (benchmark_end_price - benchmark_start_price) / benchmark_start_price * 100

        margin = change - benchmark_change
        
        #print(f'Margin over s&p: {margin}')
        #print(f'Total margin: {change}')

        changes.append(change)
        benchmark_changes.append(benchmark_change)
        margins.append(margin)
    end1 = time.time()
    print(f'test_time took {end1-start1:.2f} seconds')
    return changes, margins



def overnight_test():
    sp_list = get_sp500()
    ticker_dates = sp_starting_dates()
    restore_data(sp_list, ticker_dates)
    df = load_sp_500_data()
    dates = get_dates()
    margins_obtained = []
    margins_obtained_ultra = []
    df2 = benchmark()
    tables = time_machine(df, dates, 1)
    tables = tables[len(tables)//2:]
    for index in range(1, 100):
        try:
            print(f'Testing value {index}')
            changes, margins = test_time(tables, index, 1, df2)
            series = pd.Series(changes)
            print(pd.Series(changes).describe())
            pct_positive = (series > 0).mean() * 100
            print(f'{pct_positive:.2f}% are above 0')
            margins_obtained_ultra.append((index, series.median(), series.mean(), pct_positive))
        except Exception as e:
            print(e)
            print('Continuing...')
    for item in margins_obtained_ultra:
        print(item)
        
    pd.DataFrame(margins_obtained_ultra, columns=['n', 'median', 'mean', 'positives']).to_csv('shorting1.csv', index=False)
        

if __name__ == '__main__':

    order = input('Order: ') 
    overnight_test()



        
end = time.time()
h, r = divmod(end-start, 3600)
m, s = divmod(r, 60)
print(f'Operation took {h} hours {m} minutes and {s} seconds')
input('Press enter to exit')
