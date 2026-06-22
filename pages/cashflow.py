from nicegui import app, ui
import balance

class CashFlowPage:
    def __init__(self, ticker):
        txt = str(balance.get_income(ticker))
        ui.html(f'<pre>{txt}</pre>')
