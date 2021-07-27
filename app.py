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
    cur.execute("SELECT cat_key, cat_name FROM categories ORDER BY cat_key")  # query for list of cats
    cat_list = cur.fetchall()  # list of all cats
    conn.close()

    # CATEGORY ADDING FORM
    # if the form on the page wants to return data
    if request.method == "POST":  # and is_logged_in(): # remove comment once login done
        cat_name = request.form["cat_name"].strip().title()

        # checking if cat_name is a duplicate of an existing category name
        is_duplicate = False

        # initiate db connection
        conn = create_conn(DB_NAME)
        cur = conn.cursor()

        # selecting a key value pair of all māori words that match the input mri_word
        cur.execute("SELECT cat_key, cat_name FROM categories WHERE cat_name=?", (cat_name,))
        duplicate_cats = cur.fetchall()
        if duplicate_cats:  # if duplicate_cats has a value, i.e. if there are duplicate categories
            is_duplicate = True

        if not is_duplicate:
            if len(cat_name) < 3:
                return redirect("/?error=Name+must+be+at+least+3+letters+long")
            else:
                # try to add to categories table
                try:
                    cur.execute("INSERT INTO categories (cat_key, cat_name) VALUES(NULL, ?)", (cat_name,))  # insert cat_name into categories in next available position
                except Exception as e:
                    return redirect("/?error=Unknown+category+error")

        # close db connection
        conn.commit()
        conn.close()

    return render_template("categories.html", logged_in=True, cat_list=cat_list)  # change to logged_in = is_logged_in() once login done


# render the words page
@app.route("/word_list/<current_cat>", methods=["GET"])
def render_word_list_page(current_cat):
    # WORD TABLE
    # DB FETCH DICTIONARY
    # initiate db connection
    conn = create_conn(DB_NAME)
    cur = conn.cursor()
    # fetch data
    cur.execute("SELECT key, mri_word, eng_word, level, cat_key, def_key, img_name FROM dictionary WHERE cat_key=? ORDER BY key", (current_cat,))  # query for dictionary
    db_word_list = cur.fetchall()  # list of all words in this category
    # close db connection
    conn.close()

    # DATA PROCESSING
    # variables
    web_word_list = []  # the list of words that is sent to the html page
    for db_word in db_word_list:
        web_word = [db_word[1], db_word[2],
                    db_word[3]]  # creates list to pass to webpage including Māori word, English word, Level

        # DB FETCH CATEGORY AND DEFINITION
        cat_key = db_word[4]
        def_key = db_word[5]
        # initiate db connection
        conn = create_conn(DB_NAME)
        cur = conn.cursor()
        # get category from db
        cur.execute("SELECT cat_key, cat_name FROM categories WHERE cat_key=?", (cat_key,))
        cat_obj = cur.fetchall()
        cat_name = cat_obj[0][1]
        web_word.append(cat_name)  # append cat_name to web_word
        # get definition from db
        cur.execute("SELECT def_key, definition FROM definitions WHERE def_key=?", (def_key,))
        def_obj = cur.fetchall()
        definition = def_obj[0][1]
        web_word.append(definition)  # append definition to web_word
        # close db connection
        conn.close()

        # add the image name to web_word
        web_word.append(db_word[6])

        web_word_list.append(web_word)  # add the word to the list of words

    # DB FETCH CAT NAME
    # initiate db connection
    conn = create_conn(DB_NAME)
    cur = conn.cursor()
    # fetch data
    cur.execute("SELECT cat_name FROM categories WHERE cat_key=? ORDER BY cat_key LIMIT 1", (current_cat,))  # query for current category, stopping once a matching cat_key is found
    cat_obj = cur.fetchall()  # category name and key
    current_cat_name = cat_obj[0][0]
    # close db connection
    conn.close()

    return render_template("word_list.html", word_list=web_word_list, current_cat=current_cat, current_cat_name=current_cat_name)


@app.route("/add_word", methods=["GET", "POST"])
def render_add_word_page():
    # list of categories
    # initiating connection to db
    conn = create_conn(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT cat_key, cat_name FROM categories")
    cat_list = cur.fetchall()

    # ending db connection
    conn.close()

    # WORD ADDING FORM
    # if the form on the page wants to return data
    if request.method == "POST":  # and is_logged_in(): # remove comment once login done
        # text data straight from form
        mri_word = request.form["mri_word"].strip().lower()
        eng_word = request.form["eng_word"].strip().lower()
        level = request.form["level"].strip()
        cat_key = request.form["cat_key"]

        # data from form that needs to be processed
        definition = request.form["definition"].strip()

        # initiating connection to db
        conn = create_conn(DB_NAME)
        cur = conn.cursor()

        # checking if mri_word AND eng_word are duplicates of existing words
        duplicate_word_list = []
        is_duplicate = False

        # selecting a key value pair of all māori words that match the input mri_word
        cur.execute("SELECT key, mri_word FROM dictionary WHERE mri_word=?", (mri_word,))
        mri_word_list = cur.fetchall()

        # selecting a key value pair of all english words that match the input eng_word
        cur.execute("SELECT key, eng_word FROM dictionary WHERE eng_word=?", (eng_word,))
        eng_word_list = cur.fetchall()

        for i in mri_word_list:
            duplicate_word_list.append(i[0])

        for j in eng_word_list:
            for k in duplicate_word_list:
                if j[0] == k:
                    is_duplicate = True

        if not is_duplicate:  # if the word is not a duplicate, continue
            # making def_key
            def_key = 0  # defaults to 0 (No Definition)

            if definition != "":  # if there is a provided definition
                # add definition to definitions table
                try:
                    cur.execute("INSERT INTO definitions (def_key, definition) VALUES (NULL, ?)", (definition,))
                except Exception as e:
                    return redirect("/?error=Unknown+definition+adding+error")
                # fetch def_key from table
                cur.execute("SELECT def_key, definition FROM definitions ORDER BY def_key DESC LIMIT 1;")
                def_obj = cur.fetchone()
                def_key = def_obj[0]

            # inserting word to db
            try:
                cur.execute(
                    "INSERT INTO dictionary (mri_word, eng_word, level, cat_key, def_key, img_name) VALUES (?, ?, ?, ?, ?, NULL)", (mri_word, eng_word, level, cat_key, def_key))
            except Exception as e:
                return redirect("?/error=Unknown+word+adding+error")
        else:
            return redirect("?/error=Duplicate+word")

        # ending db connection
        conn.commit()
        conn.close()

    return render_template("add_word.html", logged_in=True, categories=cat_list)  # change to logged_in = is_logged_in() once login done

@app.route("/word/<key>", methods=["GET", "POST"])
def render_word_page(key):
    # get word data
    # initiating connection to db
    conn = create_conn(DB_NAME)
    cur = conn.cursor()

    # get word
    cur.execute("SELECT mri_word, eng_word, level, cat_key, def_key, img_name FROM dictionary WHERE key=?", (key, ))
    word_obj_db = cur.fetchone()

    # get category
    cur.execute("SELECT cat_name FROM categories WHERE cat_key=?", (word_obj_db[0][3], ))  # word_obj_db[0][3] == cat_key
    cat_obj_db = cur.fetchone()

    # get definition
    cur.execute("SELECT definition FROM definitions WHERE def_key=?", (word_obj_db[0][4], ))  # word_obj_db[0][3] == def_key
    def_obj_db = cur.fetchone()

    # ending db connection
    conn.close()

    # creating word_obj to send to webpage
    word_obj = [word_obj_db[0][0], word_obj_db[0][1], word_obj_db[0][2], cat_obj_db[0][0], def_obj_db[0][0], word_obj_db[0][5]]
    # in order: mri_word, eng_word, level, (all from word_obj_db); cat_name (from cat_obj_db); definition (from def_obj_db); img_name (from word_obj_db)



    return render_template("word.html", word_obj = word_obj)


def is_logged_in():
    if session.get("email") is None or session.get("password") is None:
        return False
    else:
        return True


app.run(debug=True)
