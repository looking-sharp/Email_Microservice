from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv                          #type: ignore
import os

load_dotenv()
db_link = os.getenv("DATABASE_URL")

client = MongoClient(db_link, server_api=ServerApi('1'))
db = client.email_microservice

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
