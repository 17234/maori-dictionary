from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error

from flask_bcrypt import Bcrypt

DB_NAME = "dict.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "OUH9awc8m98mch4r^&GHN^&Fv5SDF^*TI&YGn76fv675d6f7g8et5v"

MIN_CAT_NAME_LENGTH = 3
MIN_WORD_LENGTH = 1
MIN_LEVEL = 1
MAX_LEVEL = 10


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
    if request.method == "POST" and is_logged_in():
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
            if len(cat_name) < MIN_CAT_NAME_LENGTH:
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

    return render_template("categories.html", logged_in=is_logged_in(), cat_list=cat_list)


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
        web_word = [db_word[0], db_word[1], db_word[2], db_word[3]]  # creates list to pass to webpage including key, Māori word, English word, Level

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

    return render_template("word_list.html", logged_in=is_logged_in(), word_list=web_word_list, current_cat=current_cat, current_cat_name=current_cat_name)


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
    if request.method == "POST" and is_logged_in():
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

        if not is_duplicate and len(mri_word) >= MIN_WORD_LENGTH and len(eng_word) >= MIN_WORD_LENGTH:  # if the word is not a duplicate, continue
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
            return redirect("?/error=Duplicate+or+not+present+word")

        # ending db connection
        conn.commit()
        conn.close()

    return render_template("add_word.html", logged_in=is_logged_in(), cat_list=cat_list, MIN_LEVEL = MIN_LEVEL, MAX_LEVEL = MAX_LEVEL)


@app.route("/word/<key>", methods=["GET", "POST"])
def render_word_page(key):
    # get word data
    # initiating connection to db
    conn = create_conn(DB_NAME)
    cur = conn.cursor()

    # get list of all categories
    cur.execute("SELECT cat_key, cat_name FROM categories")
    cat_list = cur.fetchall()

    # get word
    cur.execute("SELECT mri_word, eng_word, level, cat_key, def_key, img_name FROM dictionary WHERE key=?", (key, ))
    word_obj_db = cur.fetchone()

    # get category of that word
    cur.execute("SELECT cat_name FROM categories WHERE cat_key=?", (word_obj_db[3], ))  # word_obj_db[0][3] == cat_key
    cat_obj_db = cur.fetchone()

    # get definition
    cur.execute("SELECT definition FROM definitions WHERE def_key=?", (word_obj_db[4], ))  # word_obj_db[0][3] == def_key
    def_obj_db = cur.fetchone()

    # ending db connection
    conn.close()

    # creating word_obj to send to webpage
    word_obj = [word_obj_db[0], word_obj_db[1], word_obj_db[2], cat_obj_db[0], def_obj_db[0], word_obj_db[5], word_obj_db[4]]
    # in order: mri_word, eng_word, level, (all from word_obj_db); cat_name (from cat_obj_db); definition (from def_obj_db); img_name, def_key (both from word_obj_db)

    # WORD EDITING FORM
    # if the form on the page wants to return data
    if request.method == "POST" and is_logged_in():
        # get definition key from form
        def_key = request.form["def_key"]

        # check if a delete is wanted
        try:
            is_delete = request.form["delete"]
        except:
            is_delete = False

        # initiating connection to db
        conn = create_conn(DB_NAME)
        cur = conn.cursor()

        # if the word is to be deleted
        if is_delete == "Delete":
            if is_admin():
                if def_key != 0:  # if there is an independent definition (ie not No Definition)
                    try:
                        cur.execute("DELETE FROM definitions WHERE def_key=?", (def_key, ))
                    except Exception as e:
                        return redirect("/?error=Definition+delete+error")
                try:
                    cur.execute("DELETE FROM dictionary WHERE key=?", (key, ))
                except Exception as e:
                    return redirect("?/error=Word+delete+error")
                return redirect("/")
            else:
                return redirect("/")

        else:  # if the word is not to be deleted
            # text data straight from form
            mri_word = request.form["mri_word"].strip().lower()
            eng_word = request.form["eng_word"].strip().lower()
            level = request.form["level"].strip()
            cat_key = request.form["cat_key"]

            # data from form that needs to be processed
            definition = request.form["definition"].strip()

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

            if not is_duplicate and len(mri_word) >= MIN_WORD_LENGTH and len(eng_word) >= MIN_WORD_LENGTH:  # if the word is not a duplicate, continue
                if definition != "No definition" and def_key == 0:  # if there is a provided definition
                    # add definition to definitions table
                    try:
                        cur.execute("INSERT INTO definitions (def_key, definition) VALUES (NULL, ?)", (definition,))
                    except Exception as e:
                        return redirect("/?error=Unknown+definition+adding+error")
                    # fetch def_key from table
                    cur.execute("SELECT def_key, definition FROM definitions ORDER BY def_key DESC LIMIT 1;")
                    def_obj = cur.fetchone()
                    def_key = def_obj[0]
                elif definition == "No definition" and def_key != 0:
                    try:
                        cur.execute("DELETE FROM definitions WHERE def_key=?", (def_key, ))
                    except Exception as e:
                        return redirect("?/error=Definition+delete+error")
                    def_key = 0
                elif definition != "No definition" and def_key != 0:
                    try:
                        cur.execute("UPDATE definitions SET definition=? WHERE def_key=?", (definition, def_key))
                    except Exception as e:
                        return redirect("?/error=Definition+update+error")

                # inserting word to db
                try:
                    cur.execute("UPDATE dictionary SET mri_word=?, eng_word=?, level=?, cat_key=?, def_key=? WHERE key=?", (mri_word, eng_word, level, cat_key, def_key, key))
                except Exception as e:
                    return redirect("?/error=Unknown+word+adding+error")
            else:
                return redirect("?/error=Duplicate+or+not+present+word")

        # ending db connection
        conn.commit()
        conn.close()

    return render_template("word.html", logged_in=is_logged_in(), word_obj = word_obj, cat_list=cat_list)


@app.route("/login", methods=["GET", "POST"])
def render_login_page():
    # fetch login info from webpage
    if request.method == "POST":
        username = request.form["username"]
        email = request.forn

    return render_template("login.html", logged_in=is_logged_in())

@app.route("/signup", methods=["GET", "POST"])
def render_signup_page():
    # fetch signup info from webpage
    if request.method == "POST":
        name = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        h_password = bcrypt.generate_password_hash(password)
        password = False  # clearing the password so that only an encrypted value is dealt with

        # initiating connection to db
        conn = create_conn(DB_NAME)
        cur = conn.cursor()

        # Duplicate checking
        duplicate_user_list = []
        is_duplicate = False

        # fetching duplicate names
        cur.execute("SELECT key, name FROM users WHERE name=?", (name, ))
        name_list = cur.fetchall()

        # fetching duplicate emails
        cur.execute("SELECT key, email FROM users WHERE email=?", (email, ))
        email_list = cur.fetchall()

        # checking if duplicate
        if len(name_list) > 0 or len(email_list) > 0:
            is_duplicate = True

        if not is_duplicate:
            try:
                cur.execute("INSERT INTO users (name, email, h_password, is_admin) VALUES (?, ?, ?, FALSE)", (name, email, h_password))
                conn.commit()
            except Exception as e:
                return redirect("?/error=User+adding+database+error")
        else:
            return redirect("?/error=That+name+or+email+is+in+use")

        # ending connection to db
        conn.close()

    return render_template("signup.html", logged_in=is_logged_in())

def is_logged_in():
    #if session.get("email") is None or session.get("password") is None:
        #return False
    #else:
        return True

def is_admin():
    return True


app.run(debug=True)
