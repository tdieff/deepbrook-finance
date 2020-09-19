import sqlit3
from helpers import lookup, get_position_value, usd
from flask import request, session

# Configure CS50 Library to use SQLite database
db = sqlite3.connect('finance.db') 

def enough_shares(shares):
    symbol = request.form.get("symbol")
    symbol = symbol.upper()
    rows = db.execute("SELECT SUM(shares) FROM trades WHERE username = :username AND symbol = :symbol GROUP BY symbol", username=session["user_username"], symbol=symbol)
    print(rows)
    if len(rows) > 0:
        shares_owned = int(rows[0]['SUM(shares)'])
        if shares_owned >= shares and rows != None:
            return True
        else:
            return False
    else:
        return False


def validate_sell():
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
        if enough_shares(shares) == True:
            return True
        else:
            error_message = "not enough shares"
            return error_message
    else:
        error_message = "must enter positive integer number of shares"
        return error_message
