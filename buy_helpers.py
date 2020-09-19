from flask import redirect, render_template, request, session
import sqlite3
from helpers import lookup, apology, cash_balance, get_position_value

# Configure CS50 Library to use SQLite database
db = sqlite3.connect('finance.db') 

def enough_cash(shares):
    stock_info = lookup(request.form.get("symbol"))
    cash = cash_balance()
    cost = get_position_value(stock_info, shares)
    if cash >= cost:
        return True
    else:
        return False


def place_order(order_type):
    cash = cash_balance()
    shares = int(request.form.get("shares"))
    stock_info = lookup(request.form.get("symbol"))
    value = get_position_value(stock_info, shares)
    if order_type == 'sell':
        shares *= -1
        cash += value
    else:
        cash -= value
    db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash=cash, user_id=session["user_id"])
    db.execute("INSERT INTO trades (username, symbol, price, shares, order_time) VALUES (:username, :symbol, :price, :shares, (SELECT datetime('now')))", username=session["user_username"], symbol=stock_info["symbol"], price=stock_info["price"], shares=shares)
    return stock_info, shares


def validate_buy():
    if not request.form.get("symbol"):
        error_message = "must enter ticker symbol"
        return error_message
    elif lookup(request.form.get("symbol")) == None:
        error_message = "invalid ticker symbol"
        return error_message
    elif not request.form.get("shares"):
        error_message = "must enter positive integer number of shares"
        return error_message
    else:
        shares = request.form.get("shares")
    if shares.isdigit() and int(shares) > 0:
        shares = int(shares)
        if enough_cash(shares) == True:
            return True
        else:
            error_message = "not enough cash"
            return error_message
    else:
        error_message = "must enter positive integer number of shares"
        return error_message
