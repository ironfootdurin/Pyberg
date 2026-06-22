from nicegui import app, ui
from .misc import start_updater, ticker_is_valid
import find
import user





class CompanyCard:
    def __init__(self, ticker):
        
        self.quantity = 1
        self.expanded = False
        self.ui_data = {'ticker': ticker,
               'price': 'Loading...',
               'name': 'Loading...',
               'sector': 'Loading...',
               'description': 'Loading...',
               'valuation': 0, 
               'config': {
            'xAxis': {'type': 'time'},
            'yAxis': {'type': 'value'},
            'series': [{'type': 'line', 'data': [[1,1], [2,2]]}]
            },
                'config2': {
            'xAxis': {'type': 'time'},
            'yAxis': {'type': 'value'},
            'series': [{'type': 'line', 'data': [[1,1], [2,2]]}]
            },
                        
               }
        start_updater()
        with ui.row():
            with ui.card().classes('bg-secondary shadow-xl p-6 rounded-2xl w-3/4'):
                with ui.row().classes('w-full justify-between'):
                    label_2 = ui.label().bind_text_from(self.ui_data, 'name').classes('text-xl')
                    label_3 = ui.label().bind_text_from(self.ui_data, 'sector')                   
                label_1 = ui.label().bind_text_from(self.ui_data, 'price').classes('text-sm')
                label_4 = ui.label().bind_text_from(self.ui_data, 'description').classes('text-sm text-justify line-clamp-3')
                label_4_btn = ui.label('Read more').classes('text-xs text-primary fonr-bold mt-1 cursor-pointer')
                label_4_btn.on('click', lambda: [
                label_4.classes(toggle='line-clamp-3'), 
                label_4_btn.set_text('Read more' if 'line-clamp-3' in label_4._classes else 'Read less')])
                    
                ui.timer(10.0, self.get_recent_price)
                self.chart = ui.echart(options=self.ui_data['config']).classes('w-full h-96')
                self.chart2 = ui.echart(options=self.ui_data['config2']).classes('w-full h-96')

                with ui.row().classes('w-full'):
                    ui.number(label='Volume of stocks', value=1, format='%.2f',
                              on_change=lambda e: self.save_quantity(e))
                    ui.button('Buy', on_click=self.handle_buy).classes('w-full bg-info text-white py-2')
                    
            with ui.card().classes('bg-secondary shadow-xl p-6 rounded-2xl flex-grow'):
                ui.label('Quaterly Report:').classes('text-lg')
                ui.link('View quaterly report', f'/report/{ticker}', new_tab=True)
                ui.label('Cash Flow Statement:').classes('text-lg')
                ui.link('View cash flow statement', f'/balance/{ticker}', new_tab=True)
                
        self.get_recent_price()
    def save_quantity(self, e):
        self.quantity = e.value

    def get_recent_price(self):
        try:
            ticker = self.ui_data['ticker']
            ticker = ticker.strip().upper()
            verify = ticker_is_valid(ticker)
            if verify:
                price, refresh = find.recent_prices(ticker)
                if price and price[0] is not None:
                    self.ui_data['price'] = f"$ {round(price[0], 2)}"
                    self.ui_data['valuation'] = price
                else:
                    self.ui_data['price'] = f"Fetching live price for {ticker}... "

                name = find.name(ticker)
                self.ui_data['name'] = name[0] if name else "Unavailable"

                sector = find.sector(ticker)
                self.ui_data['sector'] = sector[0] if sector else "Unavailable"

                description = find.description(ticker)
                self.ui_data['description'] = description[0] if description else "Unavailable"

                data = find.monthly_data(ticker)

                config = find.nicegui_graph(data, ticker)
                self.ui_data['config'] = config
                self.chart.options.clear()
                self.chart.options.update(config)
                self.chart.update()

                data2 = find.daily_data(ticker)

                config2 = find.nicegui_graph(data2, ticker)
                self.ui_data['config2'] = config2
                self.chart2.options.clear()
                self.chart2.options.update(config2)
                self.chart2.update()
                                              
        except Exception as e:
            print(f'Error: {e}')
            return
        
    def handle_buy(self):
        username = app.storage.user.get('username')
        ticker = self.ui_data['ticker']
        price, refresh = find.recent_prices(ticker)
        stock_price = price
        if refresh:
            ui.notify(f'Stock price still refreshing. please wait', type = 'warning')
            return

        result = user.buy_stock(username, ticker, self.quantity, stock_price[0])

        if result:
            ui.notify(f'{self.quantity} stocks of {self.ui_data["name"]} successfully bought!', type = 'positive')
        else:
            ui.notify('Not enough money!', type = 'negative')
