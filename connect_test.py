import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()
import os
uri = os.getenv("MONGODB_URI")

# Tell PyMongo to use certifi's certificate bundle
client = MongoClient(uri, tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("Successfully connected with SSL verification!")
except Exception as e:
    print(f"Still failing: {e}")
