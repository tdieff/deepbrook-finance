from flask_sqlalchemy import SQLAalchemy
from helpers import lookup, get_position_value, usd
from flask import session

# Configure to use SQLite database
db_name = 'finance.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app) 

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
