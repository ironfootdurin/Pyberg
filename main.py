from pages import NavBar, CompanyCard, HomePage, LoginPage, SignUpPage, CashFlowPage, ResearchPage
from pages.misc import check_login, Theme, start_updater, forward_quarterly, forward_update
from nicegui import app, ui
import user
import asyncio
from pathlib import Path
import weekly_running

@ui.page('/company/{ticker}')
def company_page(ticker):
    if not check_login():
        return
    Theme()
    start_updater()
    NavBar()
    CompanyCard(ticker)

@ui.page('/report/{ticker}')
async def forwarding(ticker):
    if not check_login():
        return
    Theme()
    ui.label('Loading report...')
    ui.spinner()
    client = ui.context.client
    asyncio.create_task(forward_quarterly(ticker, client))

@ui.page('/balance/{ticker}')
def cashflow_page(ticker):
    if not check_login():
        return
    Theme()
    CashFlowPage(ticker)

@ui.page('/research')
def research_page():
    if not check_login():
        return
    Theme()
    NavBar()
    ResearchPage()



@ui.page('/home')
def home_page():
    if not check_login():
        return
    Theme()
    start_updater()
    NavBar()
    HomePage()
    

@ui.page('/signup')
def signup_page():
    Theme()
    SignUpPage()

@ui.page('/update')
def update_page():
    ui.label('Updater')
    ui.label('Updating research...')
    ui.spinner()
    client = ui.context.client
    asyncio.create_task(forward_update(client))
    
@ui.page('/')
def login_page():
    Theme()
    LoginPage()

if __name__ in {'__main__', '__mp_main__'}:
    user.connect()
    secure_key = '3kB5pQ_BEAsYWw4j6d3ehBbr0eXTCMHJEn_9WKhKJUc='
    app.add_static_files('/reports', str(Path(__file__).parent / 'temp' / 'filings'))
    ui.run(host = '0.0.0.0', port = 8080, storage_secret = secure_key)



    
