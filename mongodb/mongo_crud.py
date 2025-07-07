from pymongo import MongoClient
import os

# Use Mongo URI from environment variable or Streamlit secrets
MONGO_URI = os.getenv("MONGO_URI", "your-default-mongodb-uri")
client = MongoClient(MONGO_URI)
db = client.get_default_database()

# ✅ Insert many records (SYNC)
def insert_bulk_alarms(records, collection_name):
    if not records:
        return []
    collection = db[collection_name]
    result = collection.insert_many(records)
    return result.inserted_ids

# ✅ Fetch open alarms (SYNC)
def get_open_alarms(collection_name):
    collection = db[collection_name]
    return list(collection.find({"EsclationStatus": "OPEN"}))
