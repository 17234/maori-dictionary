from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error

from flask_bcrypt import Bcrypt

DB_NAME = "dict.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "OUH9awc8m98mch4r^&GHN^&Fv5SDF^*TI&YGn76fv675d6f7g8et5v"


# create a connection to the database
def create_conn(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as err:
        print(err)

    return None


@app.route("/", methods=["GET", "POST"])
def render_index():
    if request.method == "POST" and is_logged_in():
        cat_name = request.form["cat_name"].strip().title()
        if len(cat_name) < 3:
            return redirect("/?error=Name+must+be+at+least+3+letters+long")
        else:
            # connect to db



def is_logged_in():
    if session.get("email") is None or session.get("password") is None:
        return False
    else:
        return True
