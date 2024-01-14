from functools import wraps
import sys
import os
from flask import Flask, render_template, redirect, request, url_for, session, make_response
from pyrebase import initialize_app
import json
from dotenv import load_dotenv
load_dotenv()

config = {
  "apiKey": "AIzaSyCM-EXCy1aYMZWiZmcGg8W5hiJ3WOxh8tQ",
  "authDomain": "note-e2a87.firebaseapp.com",
  "projectId": "note-e2a87",
  "storageBucket": "note-e2a87.appspot.com",
  "messagingSenderId": "177399568707",
  "appId": "1:177399568707:web:4550898e54b9ee87d437f6",
  "databaseURL" : "https://note-e2a87-default-rtdb.firebaseio.com/"
}

firebase = initialize_app(config)

auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

app = Flask(__name__)
app.secret_key = os.urandom(24)

def isAuthenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth.current_user != None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# index route
@app.route("/")
def index():
    user = auth.current_user
    if user:
        user_data = db.child("users").child(user['localId']).get()
        profile_id = user['localId']
        all_achivements = db.child("Achivements").get().each()
        if user_data.val() is not None:
            user_data = user_data.val()
            if user_data.get('profile_filled'):
                return render_template("index.html", id=profile_id, all=all_achivements)
            else:
                return redirect('/edit_profile/' + profile_id)
    else:
        all_achivements = []  # Initialize as an empty list when the user is not logged in
        return render_template('index.html', all=all_achivements)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        usr_pwd = request.form["pwd"]
        rptpwd = request.form["rptpwd"]
        if usr_pwd == rptpwd:
            try:
                email = request.form["usr_email"]
                password = request.form["rptpwd"]
                user = auth.create_user_with_email_and_password(email, password)
                auth.send_email_verification(user['idToken'])
                auth.get_account_info(user['idToken'])
                user_id = user['idToken']
                local_id = user['localId']
                user_email = email
                session["email"] = user_email
                session['local'] = local_id
                session['usr'] = user_id
                data = {"email": email, "profile_filled": False}
                db.child("users").child(local_id).set(data, user['idToken'])
                acc_create = "Your account has been created successfully!"
                return render_template("login.html", acc_create=acc_create)
            except Exception as e:
                error_json = e.args[1]
                error = json.loads(error_json)['error']['message']
                error = error.replace('_', ' ')
                error = ('{}'.format(error))
                return render_template('signup.html', error=error)
        elif usr_pwd != rptpwd:
            pass_match = "Both Passwords Not Matched"
            return render_template('signup.html', pass_mass=pass_match)
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['usr_email']
        password = request.form["rptpwd"]

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            account_info = auth.get_account_info(user['idToken'])
            user_id = user['idToken']
            local_id = user['localId']
            user_email = email
            if account_info['users'][0]['emailVerified'] == True:
                session['usr'] = user_id
                session["email"] = user_email
                session['local'] = local_id
                return redirect(url_for('index'))
            else:
                not_verified = "Please Verify Your Email"
                return render_template("login.html", not_verified=not_verified)
        except Exception as e:
            error_json = e.args[1]
            error = json.loads(error_json)['error']['message']
            error = error.replace('_', ' ')
            error = ('{}'.format(error))
            return render_template('login.html', error=error)
    return render_template("login.html")

@app.route("/create", methods=["GET", "POST"])
@isAuthenticated
def create():
    user = auth.current_user
    local_id = user['localId']
    if request.method == "POST":
        profile_pic_url = storage.child("profile_pic/" + local_id).get_url(None)
        user_title = db.child("users").child(user['localId']).child('title').get()
        user_name = db.child("users").child(user['localId']).child('name').get()
        user_title = user_title.val()
        name = user_name.val()
        title = request.form["a_title"]
        date = request.form["a_date"]
        link = request.form["a_link"]
        achivement = {
            'name': name,
            'profile_pic': profile_pic_url,
            'user_title': user_title,
            'title': title,
            'date': date,
            'link': link,
            "author": session["email"]
        }
        title = title.replace(" ", "-")
        try:
            db.child("Achivements").child(title).set(achivement, user['idToken'])
            return redirect("/")
        except Exception as e:
            error_json = e.args[1]
            error = json.loads(error_json)['error']['message']
            error = error.replace('_', ' ')
            error = ('{}'.format(error))
            return render_template("create.html", message="Something went wrong")

    return render_template("create.html")

@app.route("/achivement/<id>")
def achivement(id):
    orderedDict = db.child("Achivements").order_by_key().equal_to(id).limit_to_first(1).get()
    return render_template("achivements.html", data=orderedDict)

@app.route("/edit/<id>", methods=["GET", "POST"])
@isAuthenticated
def edit(id):
    user = auth.current_user
    local_id = user['localId']
    if request.method == "POST":
        try:
            title = request.form["a_title"]
            new_title = request.form["new_title"]
            date = request.form["a_date"]
            link = request.form["a_link"]
            profile_pic_url = storage.child("profile_pic/" + local_id).get_url(None)
            user_title = db.child("users").child(user['localId']).child('title').get()
            user_name = db.child("users").child(user['localId']).child('name').get()
            user_title = user_title.val()
            name = user_name.val()
            achivement = {
                'name': name,
                'profile_pic': profile_pic_url,
                'user_title': user_title,
                'title': new_title,
                'date': date,
                'link': link,
                "author": session["email"],
            }
            new_title = new_title.replace(" ", "-")
            if new_title:
                db.child("Achivements").child(id).remove(user['idToken'])
                db.child("Achivements").child(new_title).update(achivement, user['idToken'])
                return redirect("/achivement/" + new_title)
            else:
                db.child("Achivements").child(title).update(achivement, user['idToken'])
            return redirect("/achivement/" + id)
        except Exception as e:
            error_json = e.args[1]
            error = json.loads(error_json)['error']['message']
            error = error.replace('_', ' ')
            error = ('{}'.format(error))
            return render_template("edit.html" + id, error=error)
    orderedDict = db.child("Achivements").order_by_key().equal_to(id).limit_to_first(1).get()
    return render_template("edit.html", data=orderedDict)

@app.route("/delete/<id>", methods=["POST"])
@isAuthenticated
def delete(id):
    user = auth.current_user
    db.child("Achivements").child(id).remove(user['idToken'])
    return redirect("/")

# @app.route("/edit_profile/<id>", methods=["GET", "POST"])
# @isAuthenticated
# def edit_profile(id):
#     user = auth.current_user
#     local_id = user['localId']
#     if request.method == "POST":
#         profile_pic = request.files["profile_pic"]
#         website = request.form["website"]
#         github = request.form["github"]
#         twitter = request.form["twitter"]
#         linedin = request.form["linedin"]
#         name = request.form["name"]
#         title = request.form["title"]
#         age = request.form["age"]
#         if profile_pic:
#             storage.child("profile_pic/" + local_id).put(profile_pic, user['idToken'])
#             profile_pic_url = storage.child("profile_pic/" + local_id).get_url(None)
#         else:
#             profile_pic_url = storage.child("profile_pic/" + local_id).get_url(None)

#         data = {
#             "profile_filled": True,
#             "profile_pic": profile_pic_url,
#             "website": website,
#             "github": github,
#             "twitter": twitter,
#             "linedin": linedin,
#             "name": name,
#             "title": title,
#             "age": age
#         }
#         db.child("users").child(id).update(data, user['idToken'])
#         return redirect("/profile/" + id)
#     orderedDict = db.child("users").order_by_key().equal_to(id).limit_to_first(1).get()
#     return render_template("edit_profile.html", data=orderedDict)
import uuid

def generate_unique_filename(filename):
    unique_id = str(uuid.uuid4())
    extension = filename.rsplit('.', 1)[1].lower()
    return f"{unique_id}.{extension}"

@app.route("/edit_profile/<id>", methods=["GET", "POST"])
@isAuthenticated
def edit_profile(id):
    user = auth.current_user
    local_id = user['localId']
    if request.method == "POST":
        try:
            # Check if a file was uploaded
            if 'profile_pic' in request.files:
                profile_pic = request.files["profile_pic"]
                # Ensure the file has an allowed extension (e.g., .jpg, .png)
                if profile_pic and allowed_file(profile_pic.filename):
                    # Generate a unique filename (you can use UUID or other methods)
                    unique_filename = generate_unique_filename(profile_pic.filename)
                    # Upload the file to Firebase Storage
                    storage.child("profile_pic/" + local_id + "/" + unique_filename).put(profile_pic, user['idToken'])
                    # Get the URL of the uploaded image
                    profile_pic_url = storage.child("profile_pic/" + local_id + "/" + unique_filename).get_url(None)
                else:
                    return render_template("edit_profile.html", error="Invalid file format. Allowed formats are .jpg and .png")

            else:
                # If no file was uploaded, use the existing profile_pic URL
                profile_pic_url = db.child("users").child(id).child("profile_pic").get().val()

            website = request.form["website"]
            github = request.form["github"]
            twitter = request.form["twitter"]
            linkedin = request.form["linkedin"]
            name = request.form["name"]
            title = request.form["title"]
            age = request.form["age"]

            data = {
                "profile_filled": True,
                "profile_pic": profile_pic_url,
                "website": website,
                "github": github,
                "twitter": twitter,
                "linkedin": linkedin,
                "name": name,
                "title": title,
                "age": age
            }

            db.child("users").child(id).update(data, user['idToken'])
            return redirect("/profile/" + id)
        except Exception as e:
            error_json = e.args[1]
            error = json.loads(error_json)['error']['message']
            error = error.replace('_', ' ')
            error = ('{}'.format(error))
            return render_template("edit_profile.html", error=error)

    orderedDict = db.child("users").order_by_key().equal_to(id).limit_to_first(1).get()
    return render_template("edit_profile.html", data=orderedDict)

@app.route("/profile/<id>")
@isAuthenticated
def profile(id):
    orderedDict = db.child("users").order_by_key().equal_to(id).limit_to_first(1).get()
    return render_template("profile.html", data=orderedDict)
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/resend", methods=["GET", "POST"])
def resend():
    user = auth.current_user
    if user:
        try:
            auth.send_email_verification(user['idToken'])
            return render_template("login.html", resend_email="Resend Verification Mail Successfully!")
        except:
            return redirect(url_for('login'))
    return render_template('index.html')

@app.route("/forget", methods=["GET", "POST"])
def forget():
    if request.method == "POST":
        email = request.form["email"]
        try:
            auth.send_password_reset_email(email)
            return render_template("forget.html", s_error="Password reset email sent successfully!")
        except:
            return render_template("forget.html", f_error="Invalid email address")
    return render_template("forget.html")

@app.route('/logout')
def logout():
    auth.current_user = None
    session.clear()
    response = make_response(redirect('/login'))
    response.delete_cookie('session_id')
    return response

if __name__ == "__main__":
    app.run(port=5001, debug=True)
