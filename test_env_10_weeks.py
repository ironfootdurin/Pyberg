#testing environment

import sqlite3
import pandas as pd
import time
from datetime import timedelta
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
import cProfile
import pstats
import io

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
        
def choose(merged, n, b):
        chosen = merged.sort_values('performance').iloc[b:b+n]
        chosen_list = chosen['ticker'].tolist()
        return chosen_list, chosen
    

def test_time(tables, n, w, weight, df, b):
    start1 = time.time()
    chunks = []
    chunk_size = max(1, 10 // w)
    
    for i in range(0, len(tables)-chunk_size, 1):
        chunks.append(tables[i:i+chunk_size])
    chosen_weights = [1]
    #0.3, 0.3, 0.15, 0.15, 0.15
    #stocks_culled = 0    

    chosen_weights += [1] * (n - len(chosen_weights))
    ttl_margins = []
    for chunk in chunks:
        margins = []
        changes = []
        benchmark_changes = []
        for date in chunk:
            date1 = date[0].index[0]
            date2 = date[2].index[0]
            merged = pd.merge(date[1], date[0], on='ticker', suffixes=('_old', '_new'))
            merged['performance'] = (merged['close_price_new'] - merged['close_price_old']) / merged['close_price_old'] * 100    

            chosen_list, chosen = choose(merged, n, b)

            result = date[2][date[2]['ticker'].isin(chosen_list)]

            merged2 = pd.merge(result, chosen, on='ticker', suffixes=('_result', '_initial'))

            merged2['result'] = (merged2['close_price'] - merged2['close_price_new']) / merged2['close_price_new'] * 100
            
            merged2['weight'] = chosen_weights

            if weight:
                merged2['weight'] = merged2['performance'].abs()
                

            #before = len(merged2)
            merged2 = merged2[merged2['result'].between(-50, 50)]
            #after = len(merged2)

            #stocks_culled += before - after

            #if len(merged2) == 0:
            #    continue

            change = np.average(merged2['result'], weights=merged2['weight'])

            dated_benchmark_start = df[df.index == date1]
            dated_benchmark_end = df[df.index == date2]
            benchmark_start_price = dated_benchmark_start['close_price'].iloc[0]
            benchmark_end_price = dated_benchmark_end['close_price'].iloc[0]

            benchmark_change = (benchmark_end_price - benchmark_start_price) / benchmark_start_price * 100

            margin = change - benchmark_change

            #if benchmark_change >= 0:
            #    continue
            
            #print(f'Margin over s&p: {margin}')

            changes.append(change)
            benchmark_changes.append(benchmark_change)
            margins.append(margin)
            
        compound_strat = np.prod([(1+m/100) for m in changes]) - 1
        compound_bench = np.prod([(1+m/100) for m in benchmark_changes]) - 1
        
        compound_return = compound_strat - compound_bench
        #average_margin = sum(margins) / len(margins)
        average_margin = compound_return*100
        
        ttl_margins.append(average_margin)

        print(f'COMPOUND MARGIN OVER S&P: {average_margin}')
        #print(f'Stocks culled: {stocks_culled}')
    end1 = time.time()
    print(f'test_time took {end1-start1:.2f} seconds')
    return average_margin, changes, benchmark_changes, ttl_margins, chunks



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
    for border in range (0, 75, 5):
        for index in range(0, 100, 5):
            if border >= index:
                continue
            try:
                print(f'Testing value {index}')
                margin, changes, benchmark_changes, ttl_margins, chunks = test_time(tables, index, 1, True, df2, border)
                series = pd.Series(ttl_margins)
                print(pd.Series(ttl_margins).describe())
                pct_positive = (series > 0).mean() * 100
                print(f'{pct_positive:.2f}% are above 0')
                margins_obtained.append((index, series.median()))
                downside_returns = np.minimum(series, 0)
                down_std = np.sqrt(np.mean(downside_returns**2))
                sortino = series.mean() / down_std
                print(f'Sortino value: {sortino}')
                margins_obtained_ultra.append((border, index, series.median(), series.mean(), pct_positive, sortino))
            except Exception as e:
                print(e)
    for item in margins_obtained:
        print(item)
    most_successful = max(margins_obtained_ultra, key=lambda item: item[2])

    pd.DataFrame(margins_obtained_ultra, columns=['border', 'n', 'median', 'mean', 'win_rate', 'sortino']).to_csv('results_positive.csv', index=False)
    print(f'MOST SUCCESSFULL: {most_successful}')
    

        


def single_run():
    sp_list = get_sp500()
     # get_sp_data(sp_list)
    ticker_dates = sp_starting_dates()
    restore_data(sp_list, ticker_dates)
    df = load_sp_500_data()
    dates = get_dates()
    print(len(dates))
    print(dates.nunique())
    tables = time_machine(df, dates, 1)
    tables = tables[len(tables)//2:]
    df2 = benchmark()
    number = 15
    number = input('How many stocks / week? ')
    print('Starting backtest...')
    pr = cProfile.Profile()
    pr.enable()
    test_time(tables, int(number), 1, True, df2, 0)
    pr.disable()
    stream = io.StringIO()
    ps = pstats.Stats(pr, stream=stream).sort_stats('cumulative')
    ps.print_stats(20)
    print(stream.getvalue())
    average_margin, changes, benchmark_changes, ttl_margins, chunks = test_time(tables, int(number), 1, True, df2, 0)
    max_index = ttl_margins.index(min(ttl_margins))
    print(chunks[max_index][0])
    print(max_index)
    series = pd.Series(ttl_margins)
    print(series.describe())
    pct_positive = (series > 0).mean() * 100
    print(f'{pct_positive:.2f}% are above 0')
    downside_returns = np.minimum(series, 0)
    down_std = np.sqrt(np.mean(downside_returns**2))
    sortino = series.mean() / down_std
    print(f'Sortino value: {sortino}')
    #plt.boxplot(ttl_margins)
    plt.hist(ttl_margins, bins=100)
    #plt.xlim(-50, 50)
    plt.xlabel('10-week outperformance %')
    plt.ylabel('Frequency')
    plt.show()


if __name__ == '__main__':

    order = input('Order: ')
    if order == '1':
        single_run()
    else:  
        overnight_test()



        
end = time.time()
h, r = divmod(end-start, 3600)
m, s = divmod(r, 60)
print(f'Operation took {h} hours {m} minutes and {s} seconds')
input('Press enter to exit')
