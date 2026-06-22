from nicegui import app, ui
import weekly_running
import find

class ResearchPage():
    def __init__(self):
        self.ticker_data = {}
        ui.button('Run Bot', on_click=self.run_bot).classes('w-full bg-info text-white py-2')
    def run_bot(self):
        print('button clicked')
        
        self.cash = 100000
        self.stocks = weekly_running.retrieve_data()
        
        print('stocks loaded')
        ui.number(label='Current balance', value=self.cash, format='%.2f',
                              on_change=lambda e: self.save_quantity(e)).props('color=white dark')

        with ui.row().classes('w-full'):
            for index in range(0, 3):
                self.stocks_chunk = self.stocks[index * 5 : index * 5 + 5]
                with ui.column().classes('flex-1'):
                    with ui.row():
                        ui.label('Stock Name').classes('w-30')
                        ui.label('Ticker').classes('w-10')
                        #ui.label('Change').classes('w-20')
                        ui.label('Weight').classes('w-10')
                        ui.label('Money to invest').classes('w-20')
             
                    for stock in self.stocks_chunk:
                        name = find.name(stock[0])
                        ticker = stock[0]
                        #change = stock[1]
                        weight = stock[2]
                        self.ticker_data[ticker] = {
                            'money': 'Loading...'}

                        with ui.row().classes('cursor-pointer').on('click', lambda t=ticker: ui.navigate.to(f'/company/{t}')):
                            ui.label(name).classes('w-30')
                            ui.label(ticker).classes('w-8')
                            #ui.label(f'{change:.2f}').classes('w-20')
                            ui.label(f'{weight:.2f}').classes('w-10')
                            ui.label('Loading...').bind_text_from(self.ticker_data[ticker], 'money').classes('w-20')

        self.reload_table_data()
        print('table created')

    def save_quantity(self, e):
        self.cash = e.value
        self.reload_table_data()

    def reload_table_data(self):
        weight_total = 0
        for stock in self.stocks:
            weight_total += stock[2]
        for stock in self.stocks:
            ticker = stock[0]
            weight = stock[2]
            money = f'{(weight / weight_total) * self.cash:.2f}'
            
            self.ticker_data[ticker]['money'] = money
                
        
        
