import sqlite3
import pandas as pd

def load_sp_500_data():
    with sqlite3.connect('S&P-500.db') as conn:
        df = pd.read_sql_query('SELECT ticker, close_price, history_date FROM weekly', conn)
        df['history_date'] = pd.to_datetime(df['history_date'], format='%Y-%m-%d')
        df = df.set_index('history_date')
        return df

def get_dates():
    with sqlite3.connect('permanent.db') as conn:
        df = pd.read_sql_query('SELECT history_date FROM price_history_monthly WHERE ticker = "SPY"', conn)
        df['history_date'] = pd.to_datetime(df['history_date'], format='%Y-%m-%d')
        df = df.set_index('history_date')
        return pd.Series(df.index)

def audit(df, dates, n=20):
    issues = []

    for i in range(1, len(dates) - 1):
        current_date = dates.iloc[i]
        prev_date = dates.iloc[i-1]
        next_date = dates.iloc[i+1]

        prev_info = df[df.index == prev_date]
        current_info = df[df.index == current_date]
        next_info = df[df.index == next_date]

        merged = pd.merge(prev_info, current_info, on='ticker', suffixes=('_old', '_new'))
        if merged.empty:
            print(f"WARNING: No overlapping tickers at {current_date.date()}, skipping.")
            continue

        merged['performance'] = (merged['close_price_new'] - merged['close_price_old']) / merged['close_price_old'] * 100
        chosen = merged.sort_values('performance').head(n)
        chosen_list = chosen['ticker'].tolist()

        result = next_info[next_info['ticker'].isin(chosen_list)]
        merged2 = pd.merge(result, chosen, on='ticker', suffixes=('_result', '_initial'))

        missing = n - len(merged2)
        if missing > 0:
            missing_tickers = set(chosen_list) - set(merged2['ticker'].tolist())
            issues.append({
                'period': str(current_date.date()),
                'missing': missing,
                'missing_tickers': missing_tickers
            })

    total_periods = len(dates) - 2
    affected = len(issues)
    total_slots_missing = sum(i['missing'] for i in issues)

    print("=" * 45)
    print("DATA QUALITY AUDIT")
    print("=" * 45)
    print(f"Total periods:           {total_periods}")
    print(f"Affected periods:        {affected} ({round(affected/total_periods*100,1)}%)")
    print(f"Total missing slots:     {total_slots_missing}")
    if affected > 0:
        print(f"Avg missing per gap:     {total_slots_missing/affected:.1f} / {n}")

    if issues:
        ticker_counts = {}
        for issue in issues:
            for t in issue['missing_tickers']:
                ticker_counts[t] = ticker_counts.get(t, 0) + 1

        print("\nTop repeat offenders:")
        for ticker, count in sorted(ticker_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {ticker}: missing {count}x")

        print("\nWorst periods:")
        for issue in sorted(issues, key=lambda x: -x['missing'])[:5]:
            print(f"  {issue['period']}: missing {issue['missing']}/{n} — {issue['missing_tickers']}")
    else:
        print("\nNo gaps found. Data looks complete.")
    print("=" * 45)

print('starting')

df = load_sp_500_data()
dates = get_dates()
audit(df, dates)

input("Press enter to exit")
