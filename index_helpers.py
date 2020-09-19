import sqlite3
from helpers import lookup, get_position_value, usd
from flask import session

# Configure CS50 Library to use SQLite database
db = sqlite3.connect('finance.db') 

def get_portfolio_data():
    portfolio = db.execute("SELECT symbol, SUM(shares) FROM trades WHERE username = :username GROUP BY symbol ORDER BY symbol", username=session["user_username"])
    portfolio_value = 0
    for row in range(len(portfolio)):
        stock_info = lookup(portfolio[row]['symbol'])
        shares = portfolio[row]['SUM(shares)']
        position_value = get_position_value(stock_info, shares)
        portfolio_value += position_value
        portfolio[row].update({'current_price': usd(stock_info["price"]), 'position_value': usd(position_value)})
    return portfolio, portfolio_value
