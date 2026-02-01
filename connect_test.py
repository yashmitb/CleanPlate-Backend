import certifi
from pymongo import MongoClient

uri = "mongodb+srv://cleanplate:cleanplatepassword@cluster0.txg2gfi.mongodb.net/?appName=Cluster0"

# Tell PyMongo to use certifi's certificate bundle
client = MongoClient(uri, tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("Successfully connected with SSL verification!")
except Exception as e:
    print(f"Still failing: {e}")
