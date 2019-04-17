from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

# GLOBAL VARIABLES
app = Flask(__name__)
app.secret_key = 'ilikecoolstuffthatisfuntodo'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)
db_name = "private_wall"

# DB LOGIC (MY OWN ORM YAY)
def getUserById(id):
   mysql = connectToMySQL(db_name)
   query = "SELECT * FROM users WHERE id=%(id)s;"
   data = {
      "id": id
   }
   # python ternary - if exists, return, otherwise return None
   user = mysql.query_db(query, data)
   return user[0] if user else None

def getUserByEmail(email):
   mysql = connectToMySQL(db_name)
   query = "SELECT * FROM users WHERE email_address=%(e)s;"
   data = {
      "e": email
   }
   # python ternary - if exists, return, otherwise return None
   user = mysql.query_db(query, data)
   return user[0] if user else None

def getUsersOther(id):
   # get all users that do not equal the id we pass
   mysql = connectToMySQL(db_name)
   query = """SELECT * 
               FROM users 
               WHERE id != %(id)s
               ORDER BY first_name;"""
   data = {
      "id": id
   }
   users = mysql.query_db(query, data)
   # python ternary - if exists, return, otherwise return None
   return users if users else None

# get messages that belong to the user
def getUserMessages():
   # don't do anything if logged in
   if(not session.get("isLoggedIn")):
      flash("You'll shoot your eye out kid")
      redirect('/')
   mysql = connectToMySQL(db_name)
   query = """SELECT m.id as message_id, m.message, m.created, u.first_name as sender_name FROM messages m
               LEFT JOIN users u on u.id = m.fk_sender
               WHERE m.fk_receiver = %(id)s AND m.deleted IS NULL;"""
   # query = """SELECT * FROM messages WHERE fk_receiver != %(id)s;"""
   data = {
      "id": session["myUserId"]
   }
   messages = mysql.query_db(query, data)
   # python ternary - if exists, return, otherwise return None
   return messages if messages else None

#delete message with certain id
def delUserMessage(id):
   # don't do anything if logged in
   if(not session.get("isLoggedIn")):
      flash("You'll shoot your eye out kid")
      redirect('/')
   mysql = connectToMySQL(db_name)
   query = """UPDATE messages
               SET deleted = NOW()
               WHERE id = %(id)s;"""
   data = {
      "id": id
   }
   mysql.query_db(query, data)
   return True

def sendUserMessage(sender_id, receiver_id, message):
   mysql = connectToMySQL(db_name)
   query = """INSERT INTO messages (fk_sender, fk_receiver, message) 
               VALUES (%(sen)s, %(rec)s, %(mes)s);"""
   data = {
      "sen": sender_id,
      "rec": receiver_id,
      "mes": message
   }
   sent_message = mysql.query_db(query, data)
   return sent_message if sent_message else None

# return the number of messages the user has sent (regardless if it was deleted)
def getNumSentMessages(id):
   mysql = connectToMySQL(db_name)
   query = """SELECT COUNT(fk_sender) as count
            FROM messages
            WHERE fk_sender = %(id)s;"""
   data = {
      "id": id
   }
   num = mysql.query_db(query, data)[0]
   return num["count"]

# Helper functions


# Routes
@app.route('/')
def index():
   if(session.get("isLoggedIn")):
      return redirect('/wall')
   else:
      return render_template("login.html")


@app.route('/logout')
def logout():
   session.clear()
   flash("Successfully Logged out!", "status")
   return redirect('/')

@app.route('/wall')
def wall():
   if(session.get("isLoggedIn")):
      user = getUserById(session["myUserId"])
      other_users = getUsersOther(session["myUserId"])
      my_messages = getUserMessages()
      sent_messages = getNumSentMessages(session["myUserId"])
      data = {
         'full_name' : user["first_name"] + " " + user["last_name"],
         'user_id' : session["myUserId"],
         'users': other_users,
         'messages': my_messages,
         'sent_messages': sent_messages
      }
      return render_template("wall.html", data = data)
   else:
      flash("You must be logged in to access this page.", "status")
      return redirect('/')

@app.route('/register')
def register():
   return render_template("register.html")


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
         return redirect('/wall')

@app.route('/messages/new', methods=['POST'])
def insert_message():
   print('user submitted form')
   print(request.form)
   if(len(request.form["messageData"]) < 5):
      flash("message must be at least 5 characters long", "message")
      redirect('/')
   if(session.get("isLoggedIn")):
      print('user logged in, adding new message')
      valid = sendUserMessage(session["myUserId"], int(request.form["receiverId"]), request.form["messageData"])
      if(valid):
         flash('Message sent to user!', 'message')
         return redirect('/wall')
      else:
         flash('Error sending message', 'message')
         return redirect('/')
   else:
      flash('You cannot access this page without being logged in.')
      return redirect('/')

@app.route('/messages/<id>/delete')
def delete_message(id):
   if(session.get("isLoggedIn")):
      delUserMessage(id)
      flash("Message deleted!", 'message')
      return redirect('/')
   else:
      flash("You'll shoot your eye out kid")
      return redirect('/')

@app.route('/register_user', methods=['POST'])
def register_user():
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
      mysql = connectToMySQL(db_name)
      user = mysql.query_db(query, values)
      flash("Successfully registered! Please log in to access the wall!")
   return redirect('/')

if __name__ == "__main__":
   app.run(debug=True)