import os, re

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_session.__init__ import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash

from helpers import apology, login_required, lookup, usd, cash_balance
from register_helpers import username_declared, username_available, password_declared, password_retyped, validate_password, insert_user
from buy_helpers import validate_buy, place_order
from index_helpers import get_portfolio_data
from sell_helpers import validate_sell

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure to use SQLite database
db_name = 'finance.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app) 

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    portfolio, portfolio_value = get_portfolio_data()
    cash = cash_balance()
    total_assets = portfolio_value + cash
    return render_template("index.html", username=session["user_username"], rows=portfolio, portfolio_value=usd(portfolio_value), cash=usd(cash), total_assets=usd(total_assets))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if validate_buy() == True:
            stock_info, shares = place_order('buy')
            return render_template("bought.html", username=session["user_username"], shares=shares, company=stock_info["name"], symbol=stock_info["symbol"], value=usd(stock_info["price"]))
        else:
            error_message = validate_buy()
            return apology(error_message, 403)
    else:
        return render_template("buy.html", username=session["user_username"])


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.engine.execute("SELECT symbol, shares, price, order_time FROM trades WHERE username = :username ORDER BY order_time DESC", username=session["user_username"])
    for row in history:
        if row['shares'] < 0:
            order_type = 'Sell'
            row['shares'] *= -1
        else:
            order_type = 'Buy'
        row.update({'shares': row['shares'], 'price': usd(row['price']), 'order_type': order_type})
    return render_template("history.html", username=session["user_username"], rows=history)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Query database for username
        rows = db.engine.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["user_username"] = rows[0]["username"]
        # Redirect user to home page
        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/login")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must enter ticker symbol", 403)
        else:
            stock_info = lookup(request.form.get("symbol"))
        if stock_info != None:
            return render_template("quoted.html",username=session["user_username"], company=stock_info["name"], symbol=stock_info["symbol"], value=usd(stock_info["price"]))
        else:
            return apology("invalid ticker symbol", 403)
    else:
        return render_template("quote.html", username=session["user_username"])


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure proper account registration (see register_helper.py)
        if username_declared() == False:
            return apology("must declare username", 403)
        elif username_available() == False:
            return apology("username already taken", 403)
        elif password_declared() == False:
            return apology("must declare password", 403)
        elif password_retyped() == False:
            return apology("must re-type password", 403)
        elif validate_password() == False:
            return apology("password must contain at least 8 characters, including at least 1 number and at least 1 symbol", 403)
        insert_user()
        # Redirect user to login page
        return redirect("/login")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
# See sell_helpers.py
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        if validate_sell() == True:
            stock_info, shares = place_order('sell')
            return render_template("sold.html", username=session["user_username"], shares=-1*shares, company=stock_info["name"], symbol=stock_info["symbol"], value=usd(stock_info["price"]))
        else:
            error_message = validate_sell()
            return apology(error_message, 403)

    else:
        return render_template("sell.html", username=session["user_username"])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

