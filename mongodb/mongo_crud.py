from mongodb.mongo_connection import db
from typing import List, Dict

# ✅ Correct function for inserting many documents
async def insert_bulk_alarms(records: List[Dict], collection_name: str):
    collection = db[collection_name]
    result = await collection.insert_many(records)
    return result.inserted_ids

# ✅ Function to fetch open alarms
async def get_open_alarms(collection_name: str):
    collection = db[collection_name]
    return await collection.find({"EsclationStatus": "OPEN"}).to_list(length=100)
