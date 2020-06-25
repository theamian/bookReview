import os
import requests

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text, func
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Check for environment variable
if not os.getenv("GR_API"):
    raise RuntimeError("GR_API is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if not "id" in session:
        return render_template("index.html")

    return render_template("index.html", indexMsg = f"Welcome, {session['username']}!")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
        
    user = request.form.get("username")
    pass1 = request.form.get("pass1")
    pass2 = request.form.get("pass2")

    if pass1 != pass2:
        return render_template("register.html", regMsg = "Your passwords didn't match, please try again")

    if db.execute("SELECT * FROM users WHERE username = :username", {"username": user}).rowcount != 0:
        return render_template("register.html", regMsg = "The username is already taken, please choose a different one")

    hpass = generate_password_hash(pass1)

    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": user, "password": hpass})
    db.commit()

    return render_template("index.html", indexMsg = "You have successfully registered for our site! Please log in")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    user = request.form.get("username")
    pass1 = request.form.get("pass1")

    row = db.execute("SELECT * FROM users WHERE username = :username", {"username": user}).fetchone()

    if row is None or not check_password_hash(row["password"], pass1):
        return render_template("login.html", loginMsg = "Invalid username and/or password")

    session["id"] = row["id"]
    session["username"] = user

    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "GET":
        return render_template("search.html")

    filter = request.form.get("filter")
    query = request.form.get("query").lower()
    like_query = "'%" + query + "%'"

    order = text(f"SELECT * FROM books where lower({filter}) LIKE {like_query}")
    results = db.execute(order).fetchall()

    if len(results) == 0:
        return render_template("search.html", searchMsg = "Hmm, we weren't able to find anything")

    return render_template("results.html", results = results)


@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):

    order = text(f"SELECT * FROM books WHERE isbn = '{isbn}'")
    book = db.execute(order).fetchone()

    if book is None:
        return render_template("search.html", searchMsg = "An error occured, please try again")

    gr_key = os.getenv("GR_API")
    pull = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key":gr_key, "isbns":book["isbn"]})

    goodreads = pull.json()
    gr_book = goodreads["books"][0]

    num_ratings_order = text(f"SELECT COUNT(rating) FROM books JOIN ratings ON ratings.book_id = books.book_id WHERE isbn = '{isbn}'")
    avg_rating_order = text(f"SELECT AVG(rating) FROM books JOIN ratings ON ratings.book_id = books.book_id WHERE isbn = '{isbn}'")

    num_ratings = db.execute(num_ratings_order).fetchone()
    avg_rating = db.execute(avg_rating_order).fetchone()
    
    review_order = text(f"SELECT * FROM users JOIN ratings ON users.id = ratings.user_id JOIN books ON ratings.book_id = books.book_id WHERE books.isbn = '{isbn}'")
    reviews = db.execute(review_order).fetchall()

    print(reviews[0]["time"]) 

    if request.method == "GET":
        return render_template("book.html", book = book, gr_book = gr_book, num_ratings = num_ratings, avg_rating = avg_rating, reviews = reviews)