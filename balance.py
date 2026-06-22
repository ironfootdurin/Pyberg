import sqlite3
import pandas as pd
from edgar import *
import yfinance as yf
from find import market_cap
import time
import numpy as np

def get_income(ticker):
    set_identity('pyberg@duck.com')
    company = Company(ticker)
    financials = company.get_financials()
    income_format = financials.income_statement()
    return income_format

def save(file, ticker):
    file = file.to_dataframe()
    with sqlite3.connect('balance_sheets.db') as conn:
        file.to_sql(ticker, conn, if_exists='replace', index=True)
    
def retrieve(ticker):
    with sqlite3.connect('balance_sheets.db') as conn:
        df = pd.read_sql(f'SELECT * FROM "{ticker}"', conn)
        return df

def indicator1(ticker):
    
    cap = market_cap(ticker)
    try:
        df = retrieve(ticker)
    except Exception as e:
        print(f'Ticker {ticker} does not exist. Moving on.')
        return 0

    concepts = [
        'us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest', 
        'us-gaap_IncomeBeforeTaxExpenseBenefit',
        'us-gaap_IncomeBeforeTaxes',
        'us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments', 
        'ifrs-full_ProfitLossBeforeTax', 
        'us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic', 
        'us-gaap_IncomeLossFromContinuingOperationsBeforeInterestExpenseInterestIncomeIncomeTaxesExtraordinaryItemsNoncontrollingInterestsNet'
        ]

    income_frame = df[df['concept'].isin(concepts)]
        
    if income_frame.empty:
        income_frame = df[df['concept'].str.contains(
            "IncomeLossFromContinuingOperationsBefore",
            na=False, 
            regex=True
            )
                          ]
        if income_frame.empty:
            print(f'No Income Before Tax found for {ticker}')
            return 0

    col = [c for c in df.columns if 'FY' in c][-1]

    income = income_frame[col].values[0]

    indicator = float(income)/float(cap)

    return indicator




def get_marketcap():
    success = 0
    fail = 0
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_marketcap (
                ticker TEXT PRIMARY KEY,
                marketcap REAL
                )
            ''')
        
        cursor.execute('select ticker from stock_details')
        companies = cursor.fetchall()
        
    total = len(companies)
    
    for company in companies:
        try:
            ticker = company[0]
            time.sleep(0.5)
            mc = yf.Ticker(ticker).info.get('marketCap')
            with sqlite3.connect('permanent.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO company_marketcap
                    (ticker, marketcap) VALUES
                    (?, ?)''', (ticker, mc))
                print(f'ticker: {ticker}, marketcap: {mc}')
                
                success += 1

                print(f'Success: #{success}/{total}') 
                
        except Exception as e:
            
            print(f'Error: {e} on ticker {ticker}')

            fail += 1

            print(f'Fail: #{fail}')

    print(f'{success} successes out of {success + fail}, {fail} failed')
            
    
def get_indicators():
    indicators = {}
    start = time.time()
    success = 0
    fail = 0
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()            
        cursor.execute('select ticker from stock_details')
        companies = cursor.fetchall()
    total = len(companies)
    
    for (ticker, ) in companies:
        try:
            print(f'getting income for {ticker}')
            #file = get_income(ticker)
            #print('Saving file')
            #save(file, ticker)
            #print('Running indicator')
            indicator = indicator1(ticker)
            indicators[ticker] = indicator
            print(f'Indicator for {ticker}: {indicator}')
            success += 1
        except Exception as e:
            print(e)
            print(f'ticker {ticker} failed')
            fail += 1
        
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS scores (ticker TEXT PRIMARY KEY, indicator REAL)')
        cursor.executemany('INSERT OR REPLACE INTO scores VALUES (?, ?)', indicators.items())
    end = time.time()

    print(f'Operation took {end - start:.2f} seconds')
    print(f'Operation had a {100*success/(fail + success):.2f}% success rate')
    input('Press enter to exit')
        
        
def retrieve_indicators():
    with sqlite3.connect('permanent.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ticker, indicator
            FROM scores
            ORDER BY indicator DESC
            ''')
        results = cursor.fetchall()
        return results
    
def find_safe_indicators(data):
    df = pd.DataFrame(data, columns=['ticker', 'indicator'])

    filtered = df[
        (df['indicator'] > df['indicator'].median()) &
        (df['indicator'] < df['indicator'].quantile(0.9))
        ]
    return filtered



if __name__ == '__main__':
    action = input('what to do?')
    if action == '0':
        get_marketcap()
    elif action == '1':
        results = retrieve_indicators()
        filtered = find_safe_indicators(results)
        print(filtered)
    else:
        get_indicators()
        
    
