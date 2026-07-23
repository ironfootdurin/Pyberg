import weekly_running as wr
import pandas as pd
from tabulate import tabulate
import yagmail
import os

#password = os.environ.get('KEY')


if __name__ == '__main__':
    try:
        stocks, total_weight = wr.online_run()
        print(total_weight)
        data = []
        df = pd.read_csv('beta.csv')
        beta_total = 0
        for stock in stocks:
            ticker = stock[0]
            score = ((0.66 * stock[2]) / (total_weight * stock[3])) * 100000
            data.append([ticker, score])
            beta = df[df['Ticker'] == ticker]
            if beta.empty:
                print(f'{ticker} not found')
                continue
            weight = (0.66 * stock[2] / total_weight) * 100000
            beta_score = beta['Beta_12M_Daily'].iloc[0]
            beta_result = beta_score * weight
            beta_total += beta_result
            #print(f'beta_result: {beta_result}')
            #print(f'total_weight: {total_weight}')
        email_text = tabulate(
            data,
            headers=['Ticker', 'Score'],
            tablefmt="plain"
            )
        print(email_text)
        average_beta = beta_total
        average_beta = float(f'{average_beta:.2f}')
        average_beta_text = f'Short the S&P500 for ${average_beta}'
        print(average_beta_text)
        yag = yagmail.SMTP('pyberg.server@gmail.com', 'cwqt tcid fjtl yktr')
        yag.send(
            to='arthur.mourot@gmail.com',
            subject='Stocks to invest in', 
            contents=['Invest in the following stocks:', email_text, average_beta_text]
            )
    except Exception as e:
        print(e)
    input('Press ENTER to exit. ')
    
