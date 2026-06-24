from nicegui import app, ui, Client
from report import get_quarterly
from weekly_running import setup_stocks
import os
import threading
import find
import update
import time
import asyncio
updater_started = False

class Theme:
    def __init__(self):
        ui.query('body').style('background-color: #000000; color: #E0E0E0')
        ui.colors(
            primary='#00BFFF', 
            secondary='#1A1A1A', 
            accent='#181289', 
            dark='#333333', 
            positive='#00FF00', 
            negative='#FF0000', 
            warning='#FFFF00', 
            info='#1D1A5D'
            )
        ui.query('.q-field__native, .q-field__label').style('color: #E0E0E0')

def check_login():
    try:
        if not app.storage.user.get('username'):
            ui.navigate.to('/')
            return False
        return True
    except RuntimeError:
        return False

def start_updater():
    global updater_started
    if not updater_started:
        updater = threading.Thread(target=update.update_table)
        updater.daemon = True
        updater.start()
        updater_started = True

def ticker_is_valid(ticker):
    
    if not ticker or ticker == 'NONE' or ticker == ' ':
        return False
    try:
        name = find.name(ticker)
        name = name[0]
        return name is not None and name != 'NONE'
    except Exception as e:
        return False
    
async def forward_quarterly(ticker, client):
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, get_quarterly, ticker)

    with client:
        await client.connected()
        if path is None:
            ui.notify('Could not find report')
        else:
            ui.navigate.to(f'/reports/{path}')
            ui.timer(5, lambda: path.unlink(missing_ok=True), once=True)
            
async def forward_update(client):
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, setup_stocks)

    with client:
        await client.connected()
        



        

