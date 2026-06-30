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
        spy = pd.read_sql_query('''
                SELECT ticker, close_price, history_date
                FROM price_history_monthly
                WHERE ticker = "SPY"''', conn)
        spy['history_date'] = pd.to_datetime(spy['history_date'], format='%Y-%m-%d')
        spy['benchmark_return'] = (spy['close_price'].shift(-1) - spy['close_price']) / spy['close_price'] * 100
        spy['date_index'] = range(len(spy))
        spy = spy.set_index('date_index')
        return spy
    
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
    print(' Pivoting table...')
    df = df[df.index.isin(dates)]
    pivot = df.pivot(columns='ticker', values='close_price')
    print(' Shifting table data...')
    old = pivot.shift(1)
    nxt = pivot.shift(-n)

    print(' Reformatting table data...')
    long = pivot.stack().reset_index()
    long.columns = ['history_date', 'ticker', 'close_price']
    long['close_price_old'] = old.stack().values
    long['close_price_next'] = nxt.stack().values
    print(' Getting table data performance...')
    long['performance'] = (long['close_price'] - long['close_price_old']) / long['close_price_old'] * 100
    long = long.dropna()
    print(' Assigning values to dates...')
    long['date_index'] = pd.factorize(long['history_date'])[0]
    print(' Sorting values...')
    return long.sort_values(['date_index', 'performance'])

def test_time(tables_numpy, n, w, weight, df, b, ratio):
    
    correlation = []
    #start1 = time.time()
    benchmark_returns = df['benchmark_return'].values
    ttl_margins = []
    max_date_index = max(tables_numpy.keys())
    #print(f'max_date_index: {max_date_index}')
    for start in range(max_date_index - 9):
        chunk = range(start, start + 10)
        changes = []
        margins = []
        benchmark_changes = []
        for i in chunk:
            close, close_next, perf = tables_numpy[i]
            close = close[b:b+n]
            close_next = close_next[b:b+n]
            perf = perf[b:b+n]
            
            result = (close_next - close) / close * 100
            
            #weight = np.abs(perf)
            weight = np.ones(len(perf))

            change = np.average(result, weights=weight)

            benchmark_change = benchmark_returns[i]

            #if benchmark_change < 0:
            #    continue
            #correlation.append((change, benchmark_change))

            benchmark_change = benchmark_change
            #* ratio
            
            margin = change + benchmark_change * ratio
            #print(f'Margin over s&p: {margin}')

            changes.append(change)
            benchmark_changes.append(benchmark_change)
            margins.append(margin)
            
        compound_strat = np.prod([(1+m/100) for m in changes]) - 1
        compound_bench = np.prod([(1+m/100) for m in benchmark_changes]) - 1
        
        compound_return = compound_strat + compound_bench
        #average_margin = sum(margins) / len(margins)
        average_margin = compound_return*100
        
        ttl_margins.append(average_margin)

        correlation.append((compound_strat, compound_bench))

        #print(f'COMPOUND MARGIN OVER S&P: {average_margin}')
        #print(f'Stocks culled: {stocks_culled}')
    #end1 = time.time()
    #print(f'test_time took {end1-start1:.2f} seconds')

    pd.DataFrame(correlation, columns=['strategy', 'S&P500']).to_csv('correlation2.csv', index=False)
    sp500 = np.array([x[0] for x in correlation ])
    returns = np.array([x[1] for x in correlation ])
    beta = np.cov(returns, sp500, ddof=1)[0, 1] / np.var(sp500, ddof=1)
    print(beta)
    return average_margin, changes, benchmark_changes, ttl_margins



def overnight_test():
    
    print('Getting S&P tickers...')
    sp_list = get_sp500()
    print('Sorting dates...')
    ticker_dates = sp_starting_dates()
    print('Protecting data quality...')
    restore_data(sp_list, ticker_dates)
    print('Getting S&P...')
    df = load_sp_500_data()
    print('Getting verified dates...')
    dates = get_dates()
    margins_obtained = []
    margins_obtained_ultra = []
    correlation = []
    print('Getting Benchmark...')
    df2 = benchmark()
    print('Preparing data for analysis')
    tables = time_machine(df, dates, 1)
    tables = tables.set_index('date_index', drop=False)
    print('Formatting for numpy...')
    tables_numpy = {}
    for i, group in tables.groupby(tables.index):
        tables_numpy[i] = (
            group['close_price'].values,
            group['close_price_next'].values,
            group['performance'].values
        )
    #iterations = [(border, index) for border in range (0, 0)
    #                                  for index in range(0, 100)
    #                                  if border < index]
    #for border, index in tqdm(iterations, desc="Testing Strategy"):
    border = 0
    for ratio in [x / 10 for x in range(-100, 100)]:
        try:
            index = ratio
            #tqdm.write(f'Testing value {index}')
            margin, changes, benchmark_changes, ttl_margins = test_time(tables_numpy, 32, 1, True, df2, border, ratio)
            series = pd.Series(ttl_margins)
            #tqdm.write(str(pd.Series(ttl_margins).describe()))
            pct_positive = (series > 0).mean() * 100
            #tqdm.write(f'{pct_positive:.2f}% are above 0')
            margins_obtained.append((index, series.median()))
            downside_returns = np.minimum(series, 0)
            down_std = np.sqrt(np.mean(downside_returns**2))
            if down_std != 0:
                sortino = series.mean() / down_std
            else:
                sortino = 0
            #tqdm.write(f'Sortino value: {sortino}')
            margins_obtained_ultra.append((border, index, series.median(), series.mean(), pct_positive, sortino))
            print(f'{ratio}: {pct_positive}')
        except Exception as e:
            print(e)
    for item in margins_obtained:
        print(item)
    most_successful = max(margins_obtained_ultra, key=lambda item: item[2])

    pd.DataFrame(margins_obtained_ultra, columns=['border', 'n', 'median', 'mean', 'win_rate', 'sortino']).to_csv('results_positive_ratio_getting2.csv', index=False)
    print(f'MOST SUCCESSFULL: {most_successful}')
    

        


def single_run():
    print('Getting S&P tickers...')
    sp_list = get_sp500()
    print('Sorting dates...')
    ticker_dates = sp_starting_dates()
    print('Protecting data quality...')
    restore_data(sp_list, ticker_dates)
    print('Getting S&P...')
    df = load_sp_500_data()
    print('Getting verified dates...')
    dates = get_dates()
    margins_obtained = []
    margins_obtained_ultra = []
    print('Getting Benchmark...')
    df2 = benchmark()
    print('Preparing data for analysis')
    tables = time_machine(df, dates, 1)
    tables = tables.set_index('date_index', drop=False)
    tables_numpy = {}
    for i, group in tables.groupby(tables.index):
        tables_numpy[i] = (
            group['close_price'].values,
            group['close_price_next'].values,
            group['performance'].values
        )
    #number = input('How many stocks / week? ')
    number = 32
    print('Starting backtest...')
    pr = cProfile.Profile()
    pr.enable()
    test_time(tables_numpy, 70, 1, True, df2, 0, -1)
    pr.disable()
    #for ratio in [x / 10 for x in range(-100, 100)]:
    average_margin, changes, benchmark_changes, ttl_margins = test_time(tables_numpy, int(number), 1, True, df2, 0, 0)
        #series = pd.Series(ttl_margins)
        #pct_positive = (series > 0).mean() * 100
        #print(f'{ratio}: {pct_positive:.2f}% are above 0')
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
    return pr


if __name__ == '__main__':

    order = input('Order: ')
    if order == '1':
        pr = single_run()
        stream = io.StringIO()
        ps = pstats.Stats(pr, stream=stream).sort_stats('cumulative')
        ps.print_stats(20)
        print(stream.getvalue())
    else:  
        overnight_test()



        
end = time.time()
h, r = divmod(end-start, 3600)
m, s = divmod(r, 60)
print(f'Operation took {h} hours {m} minutes and {s} seconds')
input('Press enter to exit')
