print('Importing Dependencies...')
import pandas as pd
print(' Imported Pandas')
import sqlite3
print(' Imported Sqlite3')
import seaborn as sns
print(' Imported Seaborn')
import matplotlib.pyplot as plt
print(' Imported Matplotlib')
from sklearn.linear_model import LassoCV
print(' Imported Sklearn model')
from sklearn.metrics import r2_score, mean_absolute_error
print(' Imported Sklearn metrics')
import time
print(' Imported Time')
start = time.time()
import networkx as nx
print(' Imported NetworkX')

def get_data():
    print('Importing Data...')
    with sqlite3.connect('data.db') as conn:
        df = pd.read_sql_query('''
            SELECT ticker, price, date
            FROM history
                ''', conn)
        tickers = pd.read_sql_query('''
            SELECT ticker
            FROM details
                ''', conn)
        print('Converting Data...')
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
        df = df.set_index('date')
        pivot = df.pivot(columns='ticker', values='price')
        old = pivot.shift(1)
        long = pivot.stack().reset_index()
        long.columns = ['date', 'ticker', 'price']
        long['price_old'] = old.stack().values
        long['change'] = (long['price'] - long['price_old']) / (long['price_old'] + 0.00000000000001)
        long = long.dropna()
        long['date_index'] = pd.factorize(long['date'])[0]
        print(long)
        print('Filtering Data')
        long.drop(columns=["price"], inplace=True)
        long.drop(columns=["price_old"], inplace=True)
        matrix = long.pivot(index='date', columns='ticker', values='change')
        all_weights = {}
        print('Starting AI Generation')
        for i, ticker in enumerate(tickers['ticker']):
            print(f'Generating AI {i} of {len(tickers["ticker"])}...')
            print(' Preparing Data')
            y = matrix[ticker]
            x = matrix.drop(columns=[ticker])
            y = y.dropna()
            x = x.loc[y.index]
            x = x.fillna(0)
            split = int(len(x) *0.8)
            x_train, x_test = x.iloc[:split], x.iloc[split:]
            y_train, y_test = y.iloc[:split], y.iloc[split:]

            print(' Training AI Model...')
            model = LassoCV(cv=5, max_iter=5000).fit(x_train, y_train)
            print(' Exporting Weights...')
            weights = pd.Series(model.coef_, index=x_train.columns)
            top_weights = weights[weights != 0].sort_values()
            print(' Testing AI Model...')
            predictions = model.predict(x_test)
            r2 = r2_score(y_test, predictions)
            mae = mean_absolute_error(y_test, predictions)
            print(r2, mae)
            all_weights[ticker] = weights
            elapsed = time.time() - start
            estimated_total = elapsed * len(tickers) / (i + 1)
            remaining = estimated_total - elapsed

            print(f"{ticker} done")
            print(f"    Elapsed: {elapsed:.1f}s")
            print(f"    Remaining: {remaining:.1f}s")

        print('Finished AI generation')
        weights_df = pd.DataFrame(all_weights).T
        weights_df= weights_df.fillna(0)
        weights_df.to_csv('weights.csv')
        weights_df.to_pickle('weights.pkl')

        print('Creating Graph')
        G = nx.from_pandas_adjacency(weights_df, create_using=nx.DiGraph)

        pos = nx.spring_layout(G)           # computes x,y coordinates for every node using a force-directed algorithm (like magnets — connected nodes attract, all nodes repel)

        nx.draw(G, pos, with_labels=True) 
        #top_weights.plot(kind='barh', figsize=(8, 10))
        #plt.axvline(0, color='black', linewidth=0.8)
        plt.savefig('graph.png')
        plt.show()
        #corr_matrix = matrix.corr()
        #plt.figure(figsize=(12, 10))
        #sns.clustermap(corr_matrix, cmap="coolwarm", center=0)
        #plt.show()
        input('Press ENTER to exit.')
        return all_weights
    
all_weights = get_data()
