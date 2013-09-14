import os
import sys

PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PATH + "/libnemesis/")

import subprocess
import json

import mailer
import helpers

from flask import Flask, request, url_for
from libnemesis import User, College, AuthHelper

app = Flask(__name__)


@app.route("/")
def index():
    return open(PATH + '/templates/index.html').read()

@app.route("/site/sha")
def sha():
    p = subprocess.Popen(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, cwd=PATH)
    p.wait()
    return p.stdout.read()

@app.route("/registrations", methods=["POST"])
def register_user():
    ah = AuthHelper(request)
    if ah.auth_will_succeed:
        requesting_user = ah.user
        if requesting_user.can_register_users:
            teacher_username = requesting_user.username
            college_group    = request.form["college"].strip()
            first_name       = request.form["first_name"].strip()
            last_name        = request.form["last_name"].strip()
            email            = request.form["email"].strip()
            team             = request.form["team"].strip()

            if College(college_group) not in requesting_user.colleges:
                return json.dumps({"error":"BAD_COLLEGE"}), 403

            if team not in [t.name for t in College(college_group).teams]:
                return json.dumps({"error":"BAD_TEAM"}), 403

            helpers.register_user(teacher_username,
                    college_group,
                    first_name,
                    last_name,
                    email,
                    team)
            return "{}", 202
        else:
            return json.dumps({"error":"YOU_CANT_REGISTER_USERS"}),403
    else:
        return ah.auth_error_json, 403

@app.route("/user/<userid>", methods=["GET"])
def user_details(userid):
    ah = AuthHelper(request)
    if ah.auth_will_succeed and ah.user.can_administrate(userid):
        user = User.create_user(userid)
        details = user.details_dictionary_for(ah.user)
        email_change_rq = helpers.get_change_email_request(username = userid)
        if email_change_rq is not None:
            new_email = email_change_rq['new_email']
            if new_email != details['email']:
                details['new_email'] = new_email
        return json.dumps(details), 200
    else:
        return ah.auth_error_json, 403

def request_new_email(user, new_email):
    userid = user.username

    if user.email == new_email:
        helpers.clear_new_email_request(userid)
        return

    verify_code = helpers.create_verify_code(userid, new_email)
    helpers.new_email(userid, new_email, verify_code)

    url = url_for('verify_email', email=new_email, code=verify_code, _external=True)
    email_vars = { 'name': user.first_name,
                   'url': url }
    mailer.email_template(new_email, 'change_email', email_vars)

@app.route("/user/<userid>", methods=["POST"])
def set_user_details(userid):
    ah = AuthHelper(request)
    if ah.auth_will_succeed and ah.user.can_administrate(userid):
        user_to_update = User.create_user(userid)
        if request.form.has_key("new_email") and not ah.user.is_blueshirt:
            new_email = request.form["new_email"]
            request_new_email(user_to_update, new_email)
        if request.form.has_key("new_password"):
            user_to_update.set_password(request.form["new_password"])
        if request.form.has_key("new_first_name"):
            user_to_update.set_first_name(request.form["new_first_name"])
        if request.form.has_key("new_last_name"):
            user_to_update.set_last_name(request.form["new_last_name"])
        if request.form.has_key("new_team"):
            team = request.form["new_team"]
            if (not user_to_update.is_blueshirt) and ah.user.manages_team(team):
                user_to_update.set_team(team)

        user_to_update.save()
        return '{}', 200
    else:
        return ah.auth_error_json, 403

@app.route("/colleges", methods=["GET"])
def colleges():
    ah = AuthHelper(request)
    if ah.auth_will_succeed and ah.user.is_blueshirt:
        return json.dumps({"colleges":College.all_college_names()})
    else:
        return ah.auth_error_json,403

@app.route("/colleges/<collegeid>", methods=["GET"])
def college_info(collegeid):
    ah = AuthHelper(request)
    c = College(collegeid)
    if ah.auth_will_succeed and c in ah.user.colleges or ah.user.is_blueshirt:
        response = {}
        response["name"] = c.name
        response["teams"] = [t.name for t in c.teams]
        au = ah.user
        if c in au.colleges:
            response["users"] = [m.username for m in c.users if au.can_administrate(m)]

        return json.dumps(response), 200

    else:
        return ah.auth_error_json, 403

@app.route("/verify/<email>/<code>", methods=["GET"])
def verify_email(email, code):
    """
    Verifies to the system that an email address exists, and assigns it to a user.
    Expected to be used only by users clicking links in email-verfication emails.
    Not part of the documented API.
    """

    change_request = helpers.get_change_email_request(new_email = email)

    if change_request is None:
        return "No such change request", 404

    if not helpers.is_email_request_valid(change_request):
        return "Request not valid", 410

    if change_request['verify_code'] != code:
        return "Invalid verification code", 403

    u = User(change_request['username'])
    u.set_email(change_request['new_email'])
    u.save()

    return "Email address successfully changed", 200

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
