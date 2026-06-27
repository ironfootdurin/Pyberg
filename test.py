import yfinance as yf


daily = yf.download('AAPL', period='20d', interval='1wk', progress=False)
print(daily)

    
