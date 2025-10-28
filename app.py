from flask import Flask, jsonify, redirect, url_for, render_template, request     #type: ignore
from flask_cors import CORS                             #type: ignore
from werkzeug.middleware.proxy_fix import ProxyFix
import json

app = Flask(__name__)
# Allow cross referencing from port 5000 (main)
CORS(app, origins=["http://127.0.0.1:5000"])

# Fix user IP address so we can track who requests came from. 
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

adminCode = "123"

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
    if(access_code == adminCode):
        with open("./static/email-test.json", "r", encoding='utf-8') as f:
            data = json.load(f)
        return render_template("admin.html", email_data=data)
    return redirect(url_for("index"))

@app.route('/ping')
def ping():
    return jsonify({"message": "Hello from Service 1!"})