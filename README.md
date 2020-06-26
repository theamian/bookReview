# Project 1

Web Programming with Python and JavaScript

A book review website made with HTML, CSS, Flask and SQL 
Postgresql db hosted on Heroku
Features integration with Goodreads API

If you ping /api/{isbn}, where {isbn} is the ISBN of a book, you'll get a JSON response like:
{
    "title":"Antigone",
    "author":"Jean Anouilh",
    "year":"1944",
    "isbn":"041330860X",
    "review_count":2,
    "average_score":3.00
}

If the ISBN is not in the db, you're receive a {"error":"ISBN not in database"} and a 404 status code