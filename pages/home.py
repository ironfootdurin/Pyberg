from nicegui import app, ui
import pandas as pd
import user
import find

class HomePage:
    def __init__(self):
        
        self.errors_occurred = 0

        username = app.storage.user['username']
        
        homepage_data = {
            'price': user.get_cash(username), 
            'account_value': user.get_value(username)
            }
        self.portfolio_data = {
             # 'ticker': {'price': 'current_stock_price', 'change': 'percentage_change'}
            }
        self.account_data(homepage_data)
        self.portfolio_table(username)
        self.company_finder()
        
    def account_data(self, homepage_data):
        with ui.card().classes('flex bg-secondary gap-1 p-2'):
            label_2 = ui.label(f"Account Value: ${homepage_data['account_value']:,.2f}").classes('text-2xl text-primary')
            label_3 = ui.label(f"Current Cash: ${homepage_data['price']:,.2f}").classes('text-xl text-primary')


    def portfolio_table(self, username):
        portfolio = user.get_portfolio(username)
        if not portfolio:
            return
        with ui.column():
            with ui.row():
                ui.label('Stock Name').classes('w-20')
                ui.label('Ticker').classes('w-20')
                ui.label('Current Price').classes('w-20')
                ui.label('Stock Volume').classes('w-20')
                ui.label('Buying Price').classes('w-20')
                ui.label('Percentage Change').classes('w-20')
                ui.label('Buying date').classes('w-20')
                ui.label('Sell').classes('w-20')
     
        for stock in portfolio:
            ticker = stock[0]
            self.portfolio_data[ticker] = {'price': 'Loading...', 'change': 'Loading...'}
            stock_name = find.name(ticker)
            stock_volume = stock[1]
            recent_price = find.recent_prices(ticker)
            self.portfolio_data[ticker]['price'] = f'{recent_price[0][0]:.2f}'
            buying_price = stock[2]
            self.portfolio_data[ticker]['change'] = f'{float(self.portfolio_data[ticker]["price"])/float(buying_price):.2f}'
                                    
            buying_date = stock[3]

            with ui.row().classes('cursor-pointer').on('click', lambda t=ticker: ui.navigate.to(f'/company/{t}')):
                ui.label(stock_name[0]).classes('w-20')
                ui.label(ticker).classes('w-20')
                ui.label('Loading...').bind_text_from(self.portfolio_data[ticker], 'price').classes('w-20')
                ui.label(stock_volume).classes('w-20')
                ui.label(f'{buying_price:.2f}').classes('w-20')
                ui.label('Loading...').bind_text_from(self.portfolio_data[ticker], 'change').classes('w-20')
                ui.label(buying_date).classes('w-20')
                ui.button('Sell').classes('w-20').on('click.stop', lambda t=ticker, b=buying_date, s=stock_volume: self.sell_stock(username, t, b, s, self.portfolio_data[ticker]['price']))
                

        
    def sell_stock(self, username, t, b, s, p):
        result = user.sell_stock(username, t, b, s, p)
        if result:
            ui.notify('Stock sold.', type = 'positive')
            ui.navigate.reload()
        else:
            ui.notify('Failed', type = 'negative')
            
   
    def company_finder(self):
        with ui.card().classes('flex bg-secondary'):
            self.ticker_input = ui.input(label = 'Company', on_change=lambda e: self.company_finder_results(e.value))
            self.results_container = ui.column()
    def company_finder_results(self, query):
        self.results_container.clear()
        if query:
            results = find.find(query)
            if results:
                for comp in results:
                    name = find.name(comp)
                    sector = find.sector(comp)
                    if not name or not name[0] or not sector or not sector[0]:
                        continue
                    with self.results_container:
                        with ui.row().classes('justify-between flex w-full bg-secondary border border-accent p-2 cursor-pointer')\
                        .on('click', lambda c=comp: ui.navigate.to(f'/company/{c}')):
                            with ui.column().classes('gap-1 p-2'):
                                ui.label(name[0].title()).classes('text-lg text-primary')
                                ui.label(comp).classes('text-sm text-primary')
   
                            ui.label(sector[0].title() if sector else 'Unknown').classes('text-primary')

