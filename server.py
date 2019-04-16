from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = 'ilikecoolstuffthatisfuntodo'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)

def getLanguages():
   mysql = connectToMySQL("flask_survey")
   return mysql.query_db("SELECT * FROM languages;")

def getLocations():
   mysql = connectToMySQL("flask_survey")
   query = "SELECT * FROM locations;"
   return mysql.query_db(query)

def getUserById(id):
   mysql = connectToMySQL("flask_login_reg")
   query = "SELECT * FROM users WHERE id=%(id)s;"
   data = {
      "id": id
   }
   return mysql.query_db(query, data)[0]

def getUserByEmail(email):
   mysql = connectToMySQL("flask_login_reg")
   query = "SELECT * FROM users WHERE email_address=%(e)s;"
   data = {
      "e": email
   }
   return mysql.query_db(query, data)[0]

def getLocation(id):
   mysql = connectToMySQL("flask_survey")
   query = "SELECT * FROM locations WHERE id=%(id)s;"
   data = {
      "id": id
   }
   return mysql.query_db(query, data)[0]

@app.route('/')
def index():
   return render_template("index.html")

@app.route('/logout')
def logout():
   session.clear()
   flash("Successfully Logged out!", "status")
   return redirect('/')

@app.route('/success')
def success():
   if(session.get("isLoggedIn")):
      user = getUserById(session["myUserId"])
      data = {
         'user_name' : user["first_name"] + " " + user["last_name"] + "!"
      }
      return render_template("success.html", success_data = data)
   else:
      flash("You must be logged in to access this page.", "status")
      return redirect('/')

@app.route('/login', methods=['POST'])
def login():
   # is the email address valid?
   if(len(request.form["emailAddress"]) < 1 or not EMAIL_REGEX.match(request.form["emailAddress"])):
      # nope, go back to GO, do NOT collect $200
      flash("Please enter a valid email address.", 'email')
      return redirect('/')
   if(len(request.form["passwordMain"]) < 1):
      # enter a password dummy
      flash("Please enter a password.", 'password')
      return redirect('/')
   # query the DB and try to grab the user (if it exists)
   user = getUserByEmail(request.form["emailAddress"])
   if (not user):
      # no user redirect( found, you dummy
      flash("Email doesn't exist. Try again or register an account.", 'email')
      return redirect('/')
   else:
      # user exists in th DB, lets check the password
      if(not bcrypt.check_password_hash(user["password"], request.form["passwordMain"])):
         # password does not match
         flash("Password is not valid. Check your spelling and try again.", "password")
         return redirect('/')
      else:
         #password is good, lets save the userid and then redirect to the success page
         flash("Successfully Logged in!")
         session["myUserId"] = user["id"]
         session["isLoggedIn"] = True
         return redirect('/success')

@app.route('/register', methods=['POST'])
def result():
   print('user submitted form')
   print(request.form)
   query = """INSERT INTO users (first_name, last_name, email_address, password) 
               VALUES (%(fname)s, %(lname)s,%(email)s, %(password)s);"""
   if(len(request.form["firstName"]) < 2):
      flash("Please enter a first name", 'firstname')
   if(len(request.form["lastName"]) < 2):
      flash("Please enter a last name", 'lastname')
   if(len(request.form["emailAddress"]) < 1 or not EMAIL_REGEX.match(request.form["emailAddress"])):
      flash("Please enter a valid email address", 'email')
   if(request.form["passwordMain"] != request.form["passwordRepeat"]):
      flash("Passwords do not match", "passwordRepeat")
   if(len(request.form["passwordMain"]) < 8):
      flash("Please enter a password (min 8 char)", "passwordMain")
   if(len(request.form["passwordRepeat"]) < 8):
      flash("Please enter a password (min 8 char)", "passwordRepeat")

   if not '_flashes' in session.keys():
      user = getUserByEmail(request.form["emailAddress"])
      if(user):
         flash("Email already exists. Login or register with a different email address", "email")
         return redirect('/')
      values = {
         'fname': request.form["firstName"],
         'lname': request.form["lastName"],
         'email': request.form["emailAddress"],
         'password': bcrypt.generate_password_hash(request.form["passwordMain"])
      }
      mysql = connectToMySQL("flask_login_reg")
      user = mysql.query_db(query, values)
      flash("email successfully added to database!")
      session["myUserId"] = user
      session["isLoggedIn"] = True
      print(session["myUserId"])
      return redirect('/success')
   else:
      return redirect('/logout')

if __name__ == "__main__":
   app.run(debug=True)