#User Data
import sqlite3
import pandas as pd
from datetime import datetime
import time
import find
from passlib.hash import bcrypt

def connect():
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_login (
            username TEXT PRIMARY KEY,
            password TEXT,
            cash REAL
            )
            ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                username TEXT, 
                ticker TEXT, 
                stock_volume REAL,
                buying_price REAL,
                buying_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        conn.commit()

def login(username, password):
    time.sleep(0.25) #To avoid hacker spamming too quickly
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT password FROM user_login
                    WHERE username = ?''', (username, ))
            correct_password = cursor.fetchone()
            if bcrypt.verify(password, correct_password[0]):
                return True
            else:
                return False
            
        except Exception as e:
            return False

def create(username, password):
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT EXISTS (SELECT 1 FROM user_login
                WHERE username = ?)''', (username, ))
        user_exists = cursor.fetchone()[0]
        if user_exists:
            return False
        else:
            password_hashed = bcrypt.hash(password)
            cursor.execute('''INSERT OR IGNORE INTO user_login
                (username, password, cash) VALUES
                    (?, ?, 100000)''', (username, password_hashed.decode() ))
            return True

def get_cash(username):
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cash FROM user_login
                WHERE username = ?''', (username, ))
        cash = cursor.fetchone()[0]
        return cash

def get_stocks(username):
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()
        try:
            stocks = pd.read_sql_query('''SELECT * FROM user_data
                    WHERE username = ?''', conn,  params = (username,))
            return stocks
        except Exception as e:
            return None
        
def get_portfolio(username):
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, stock_volume, buying_price, buying_date FROM user_data WHERE username = ?", (username, ))
        portfolio = cursor.fetchall()
        return portfolio

    
def get_value(username):
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()
        df = pd.read_sql_query(
            'SELECT ticker, stock_volume FROM user_data WHERE username = ?',
            conn,
            params = (username, ))
        
        portfolio = df.to_dict(orient='records')

        total_value = get_cash(username)

        for stock in portfolio:
            ticker = stock['ticker']
            volume = stock['stock_volume']
            price = find.recent_prices(ticker)

            value = float(volume) * float(price[0][0])

            total_value += value
            
        return total_value       
    

def buy_stock(username, ticker, quantity, stock_price):
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()
        cash = get_cash(username)
        final_cash = cash - (float(quantity) * float(stock_price))
        if final_cash >= 0:
            cursor.execute('''UPDATE user_login SET cash = ?
                WHERE username = ? ''', (final_cash, username))
            cursor.execute('''INSERT INTO user_data
                (username, ticker, stock_volume, buying_price)
                VALUES (?, ?, ?, ? )
                    ''', (username, ticker, quantity, stock_price,))
            return True
        else:
            return False

def sell_stock(username, ticker, date, quantity, stock_price):
    with sqlite3.connect('user_info.db') as conn:
        cursor = conn.cursor()
        cash = get_cash(username)
        cursor.execute('''
            SELECT stock_volume FROM user_data
            WHERE username = ? AND buying_date = ?''', (username, date))
        try:
            quantity_available = float(cursor.fetchone()[0])
            quantity_to_sell = float(quantity)
            
        except Exception as e:
            return False
        
        if quantity_available < quantity_to_sell:
            return False
        
        if quantity_available == quantity_to_sell:
            cursor.execute('''
                DELETE FROM user_data
                WHERE username = ?
                AND buying_date = ?''', (username, date))
            conn.commit()
        else:
            new_volume = quantity_available - quantity_to_sell
            cursor.execute('''UPDATE user_data
                            SET stock_volume = ?
                            WHERE username = ?
                            AND buying_date = ?
                        ''', (new_volume, username, date))
            
        cash_gained = quantity_to_sell * float(stock_price)

        final_cash = cash_gained + cash
        
        cursor.execute('''UPDATE user_login SET cash = ?
                WHERE username = ? ''', (final_cash, username))
        conn.commit()
        return True



if __name__ == '__main__':
    connect()

        
        
        
        
        
        
