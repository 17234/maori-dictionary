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
def render_categories_page():
    # CATEGORY TABLE
    # get list of categories from db
    conn = create_conn(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT cat_key, cat_name FROM categories ORDER BY cat_key ASC") # query for list of cats
    cat_list = cur.fetchall() # list of all cats
    conn.close()

    # CATEGORY ADDING FORM
    # if the form on the page wants to return data
    if request.method == "POST": #and is_logged_in(): # remove comment once login done
        cat_name = request.form["cat_name"].strip().title()
        if len(cat_name) < 3:
            return redirect("/?error=Name+must+be+at+least+3+letters+long")
        else:
            conn = create_conn(DB_NAME)
            cur = conn.cursor()
            # try to add to categories table
            try:
                cur.execute("INSERT INTO categories (cat_key, cat_name) VALUES(NULL, ?)", (cat_name,)) # insert cat_name into categories in next available position
            except:
                return redirect("/?error=Unknown+category+error")

            conn.commit()
            conn.close()

    return render_template("categories.html", logged_in=True, cat_list=cat_list) # change to logged_in = is_logged_in() once login done

# render the categories page
@app.route("/words/<current_cat>", methods=["GET", "POST"])
def render_words_page(current_cat):
    # WORD TABLE

    # DB FETCH
    # initiate db connection
    conn = create_conn(DB_NAME)
    cur = conn.cursor()
    # fetch data
    cur.execute("SELECT key, mri_word, eng_word, level, cat_key, def_key, img_name FROM dictionary WHERE cat_key=? ORDER BY key ASC", (current_cat,)) # query for dictionary
    db_word_list = cur.fetchall() # list of all words in this category
    # close db connection
    conn.close()

    # DATA PROCESSING
    # variables
    web_word_list = [] # the list of words that is sent to the html page
    for db_word in db_word_list:
        web_word = [db_word[1], db_word[2], db_word[3]] # creates list to pass to webpage including Māori word, English word, Level

        # DB FETCH CATEGORY AND DEFINITION
        cat_key = db_word[4]
        def_key = db_word[5]
        # initiate db connection
        conn = create_conn(DB_NAME)
        cur = conn.cursor()
        # get category from db
        cur.execute("SELECT cat_key, cat_name FROM categories WHERE cat_key=?", (cat_key, ))
        cat_obj = cur.fetchall()
        cat_name = cat_obj[0][1]
        web_word.append(cat_name) # append cat_name to web_word
        # get definition from db
        cur.execute("SELECT def_key, definition FROM definitions WHERE def_key=?", (def_key, ))
        def_obj = cur.fetchall()
        definition = def_obj[0][1]
        web_word.append(definition)  # append definition to web_word
        # close db connection
        conn.close()

        # add the image name to web_word
        web_word.append(db_word[6])

        web_word_list.append(web_word) # add the word to the list of words

    # WORD ADDING FORM
    # if the form on the page wants to return data
    if request.method == "POST": #and is_logged_in(): # remove comment once login done
        # text data straight from form
        mri_word = request.form["mri_word"].strip()
        eng_word = request.form["eng_word"].strip()
        level = request.form["level"].strip()

        # data from form that needs to be processed
        definition = request.form["definition"].strip()
        image_file = request.form["image"]

        # variable reassignment
        cat_key = current_cat
        def_key = 0 # defaults to 0 (No Definition)

        # initiating connection to db
        conn = create_conn(DB_NAME)
        cur = conn.cursor()

        # making def_key
        if definition != "": # if there is a provided definition
            # add definition to definitions table
            try:
                cur.execute("INSERT INTO definitions (def_key, definition) VALUES (NULL, ?)", (definition, ))
            except:
                return redirect("/?error=Unknown+definition+adding+error")
            # fetch def_key from table
            try:
                cur.execute("SELECT * FROM tablename ORDER BY column DESC LIMIT 1;")
                def_key = cur.fetchall()
            except:
                return redirect("/?error=Unknown+definition+adding+error")
        # finding img_name

        # ending db connection
        conn.commit()
        conn.close()

    return render_template("words.html", logged_in=True, word_list=web_word_list, current_cat=current_cat) # change to logged_in = is_logged_in() once login done


def is_logged_in():
    if session.get("email") is None or session.get("password") is None:
        return False
    else:
        return True


app.run(debug=True)