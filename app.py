from flask import Flask, jsonify, redirect, url_for     #type: ignore
from flask_cors import CORS                             #type: ignore
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv                          #type: ignore
import os

load_dotenv()
db_link = os.getenv("DATABASE_URL")
app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5000"])            # Allow cross referencing from port 5000 (main)

client = MongoClient(db_link, server_api=ServerApi('1'))
db = client.email_microservice

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


@app.route("/")
def connect():
    return jsonify({"message": "Service 1 is connected"}), 200

@app.route('/ping')
def ping():
    return jsonify({"message": "Hello from Service 1!"})
