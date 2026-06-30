import weekly_running as wr
from tabulate import tabulate
import yagmail
import os

#password = os.environ.get('KEY')


if __name__ == '__main__':
    try:
        stocks, total_weight = wr.setup_stocks()
        data = []
        for stock in stocks:
            
            ticker = stock[0]
            score = (0.4 * stock[2]) / (total_weight * stock[3])
            data.append([ticker, score])
            
        
        email_text = tabulate(
            data,
            headers=['Ticker', 'Score'],
            tablefmt="plain"
            )
        print(email_text)
        yag = yagmail.SMTP('pyberg@gmail.com', 'cwqt tcid fjtl yktr')
        yag.send(
            to='arthur.mourot@gmail.com',
            subject='Stocks to invest in', 
            contents=['Invest in the following stocks:', email_text]
            )
    except Exception as e:
        print(e)
    input('Press ENTER to exit.')
    
