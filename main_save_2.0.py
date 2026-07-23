import pandas as pd
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LassoCV
from sklearn.metrics import r2_score, mean_absolute_error
import time
import networkx as nx

def get_data():
    with sqlite3.connect('data.db') as conn:
        df = pd.read_sql_query('''
            SELECT ticker, price, date
            FROM history
                ''', conn)
        tickers = pd.read_sql_query('''
            SELECT ticker
            FROM details
                ''', conn)
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
        df = df.set_index('date')
        pivot = df.pivot(columns='ticker', values='price')
        old = pivot.shift(1)
        long = pivot.stack().reset_index()
        long.columns = ['date', 'ticker', 'price']
        long['price_old'] = old.stack().values
        long['change'] = (long['price'] - long['price_old']) / long['price_old']
        long = long.dropna()
        long['date_index'] = pd.factorize(long['date'])[0]
        print(long)
        
        long.drop(columns=["price"], inplace=True)
        long.drop(columns=["price_old"], inplace=True)
        matrix = long.pivot(index='date', columns='ticker', values='change')
        all_weights = {}
        for ticker in tickers['ticker']:
            start = time.time()
            y = matrix[ticker]
            x = matrix.drop(columns=[ticker])
            
            y = y.dropna()
            x = x.loc[y.index]
            x = x.fillna(0)
            split = int(len(x) *0.8)
            x_train, x_test = x.iloc[:split], x.iloc[split:]
            y_train, y_test = y.iloc[:split], y.iloc[split:]
            model = LassoCV(cv=5, max_iter=5000).fit(x_train, y_train)
            model.score(x_train, y_train)
            weights = pd.Series(model.coef_, index=x_train.columns)
            top_weights = weights[weights != 0].sort_values()
            predictions = model.predict(x_test)
            r2 = r2_score(y_test, predictions)
            mae = mean_absolute_error(y_test, predictions)
            print(r2, mae)
            all_weights[ticker] = weights
            print(f"{ticker} done, elapsed: {time.time()-start:.1f}s, est. total: {(time.time()-start)/(list(tickers['ticker']).index(ticker)+1)*len(tickers):.1f}s")
            
        weights_df = pd.DataFrame(all_weights).T
        
        G = nx.from_pandas_adjacency(weights_df)

        pos = nx.spring_layout(G)           # computes x,y coordinates for every node using a force-directed algorithm (like magnets — connected nodes attract, all nodes repel)

        nx.draw(G, pos, with_labels=True) 
        #top_weights.plot(kind='barh', figsize=(8, 10))
        #plt.axvline(0, color='black', linewidth=0.8)
        #plt.show()
        #corr_matrix = matrix.corr()
        #plt.figure(figsize=(12, 10))
        #sns.clustermap(corr_matrix, cmap="coolwarm", center=0)
        #plt.show()
        
        return all_weights
    
all_weights = get_data()
