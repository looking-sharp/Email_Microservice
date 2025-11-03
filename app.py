from flask import Flask, jsonify, redirect, url_for, render_template, request     #type: ignore
from flask_cors import CORS                                                       #type: ignore
from werkzeug.middleware.proxy_fix import ProxyFix
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv                                                    #type: ignore
import datetime
import json
import os

app = Flask(__name__)
# Allow cross referencing from port 5000 (main)
CORS(app, origins=["http://127.0.0.1:5000"])

adminCode = "123"

@app.template_filter('friendly_datetime')
def friendly_datetime(value, format="%B %d, %Y at %I:%M %p"):
    from datetime import datetime
    if not value:
        return "NULL"
    if isinstance(value, str):
        # Convert ISO string to datetime
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.strftime(format)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/renderDebugMode", methods=["POST"])
def renderDebugMode():
    client_ip = request.remote_addr;
    print(client_ip)
    if(request.form.get("AdminCode") == adminCode):
        return redirect(url_for("adminPannel", access_code = adminCode));
    return render_template("index.html")

@app.route("/admin/<access_code>")
def adminPannel(access_code):
    if access_code != adminCode:
        return redirect(url_for("index"))
    
    view = request.args.get("view")
    if view is None:
        # Redirect to same route with view="emails"
        return redirect(url_for("adminPannel", access_code=access_code, view="emails"))

    if view == "emails":
        with open("./static/email-test.json", "r", encoding='utf-8') as f:
            data = json.load(f)
        return render_template("admin-emailsView.html", email_data=data, access_code=access_code)
    elif view == "timed_emails":
        with open("./static/timed-email-test.json", "r", encoding='utf-8') as f:
            data = json.load(f)
        return render_template("admin-timedEmailsView.html", email_data=data, access_code=access_code)




@app.route('/ping')
def ping():
    return jsonify({"message": "Hello from Email Service!"})


