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


# render the index page
@app.route("/", methods=["GET"])
def render_index():
    return render_template("index.html", logged_in=is_logged_in())

# render the categories page
@app.route("/categories", methods=["GET", "POST"])
def render_cat_page():
    # if the form on the page wants to return data
    if request.method == "POST": #and is_logged_in(): # remove comment once login done
        cat_name = request.form["cat_name"].strip().title()
        if len(cat_name) < 3:
            return redirect("/?error=Name+must+be+at+least+3+letters+long")
        else:
            print("Adding Category " + cat_name)
            # connect to db
            conn = create_conn(DB_NAME)

            # define query
            query = "INSERT INTO categories (cat_key, cat_name) VALUES(NULL, ?)"
            cur = conn.cursor()

            # execute query
            try:
                cur.execute(query, (cat_name,))
                print("Added Category " + cat_name)
            except:
                return redirect("/?error=Unknown+error")

            conn.commit()
            conn.close()

    return render_template("categories.html", logged_in=True) # change to logged_in = is_logged_in() once login done




def is_logged_in():
    if session.get("email") is None or session.get("password") is None:
        return False
    else:
        return True


app.run(debug=True)