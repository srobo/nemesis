from flask import Flask, request, url_for
import json
app = Flask(__name__)

from hashlib import sha256
from serverldap import LdapInstance
import random
import os
import sqlite3

PATH = os.path.dirname(os.path.abspath(__file__))


def handle_authentication(args,userid=None):
    if args.has_key("token"):
        token = args["token"]
        instance = LdapInstance(PATH + "/userman")
        teacher_username = get_username(token)
        teacher = instance.is_teacher(teacher_username)
        if userid is not None:
            return teacher and instance.is_teacher_of(teacher_username, userid)
        else:
            return teacher

    return False

def sqlite_connect():
    return sqlite3.connect(PATH + "/db/nemesis.sqlite")

def get_username(token):
    c = sqlite_connect()
    cur = c.cursor()
    result = cur.execute("SELECT username FROM auth WHERE token=?", (token,))
    return result.next()[0]

@app.route("/")
def index():
    return open(PATH + '/templates/index.html').read()

@app.route("/css/bootstrap.css")
def bootstrap_css():
    return open(PATH + "/static/css/bootstrap.css").read()

@app.route("/js/main.js")
def javascript():
    return open(PATH + "/static/js/main.js").read()

@app.route("/auth", methods=["POST"])
def auth():
    if request.form.has_key("username") and request.form.has_key("password"):
        username = request.form["username"]
        password = request.form["password"]
        instance = LdapInstance(PATH + "/userman")
        if instance.bind(username, password):
            if instance.is_teacher(username):
                token = str(sha256(str(random.randint(0,1000000))).hexdigest())
                auth_hash = {"token":token}

                c = sqlite_connect()
                cur = c.cursor()
                print token
                cur.execute("DELETE FROM auth WHERE token=?", (token,))
                cur.execute("INSERT INTO auth values (?,?)", (token, username))
                c.commit()
                return json.dumps(auth_hash)
            else:
                return '{"error": "not a teacher"}', 403
        else:
            return '{"error": "invalid credentials"}', 403
    return '', 403


@app.route("/deauth", methods=["POST"])
def deauth():
    deleted = False
    if request.form.has_key("token"):
        token = request.form["token"]
        c = sqlite_connect()
        cur = c.cursor()
        r = cur.execute("DELETE FROM auth WHERE token=?", (token,))
        c.commit()

        if c.total_changes == 1:
            deleted = True
        else:
            deleted = False

    if app.debug:
        return str(deleted), 200
    else:
        return '',200

@app.route("/user/<userid>", methods=["GET"])
def user_details(userid):
    if handle_authentication(request.args, userid):
        instance = LdapInstance(PATH + "/userman")
        try:
            details = instance.get_user_details(userid)
            full_name = details["Full name"] + " " + details["Surname"]
            email     = details["E-mail"]
            return json.dumps({"full_name":full_name, "email":email}), 200
        except:
            return '["error":"an error occured"}', 500
    return '{}', 403

@app.route("/user/<userid>", methods=["POST"])
def set_user_details(userid):
    if handle_authentication(request.form, userid):
        instance = LdapInstance(PATH + "/userman")
        if request.form.has_key("email"):
            instance.set_user_attribute(userid, "mail", request.form["email"])
        if request.form.has_key("password"):
            instance.set_user_password(userid, request.form["password"])
        return '{}', 200

    return '{}', 403

@app.route("/college", methods=["GET"])
def college_list():
    if handle_authentication(request.args):
        instance = LdapInstance(PATH + "/userman")
        teacher_username = get_username(request.args["token"])
        college_group = instance.get_college(teacher_username)
        college_name  = instance.get_college_name(college_group)
        college_users = instance.get_group_users(college_group)
        obj = {}
        obj["college_name"] = college_name
        obj["userids"] = college_users
        return json.dumps(obj), 200

    return "{}", 403

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
