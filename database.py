import os
from pymongo import MongoClient

# Heroku ke Config Vars se MONGO_URI automatic uthayega
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ Error: Heroku Settings -> Config Vars mein MONGO_URI nahi mila!")

client = MongoClient(MONGO_URI)
db = client["telegram_bot_db"]

settings_col = db["settings"]
slots_col = db["slots"]
users_col = db["users"]

# Initialize default slots if not present in MongoDB
if slots_col.count_documents({}) == 0:
    for i in range(1, 8):
        slots_col.insert_one({"id": i, "chat_id": "", "name": f"Channel {i}", "link": ""})

def set_setting(key, value):
    settings_col.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

def get_setting(key):
    res = settings_col.find_one({"key": key})
    return res["value"] if res else ""

def get_db(query, params=(), commit=False):
    query_lower = query.strip().lower()
    
    # Total users count
    if "select count(*) from users" in query_lower:
        count = users_col.count_documents({})
        return [[count]]
        
    # Select all users for broadcast
    elif "select user_id from users" in query_lower:
        users = users_col.find({}, {"user_id": 1})
        return [[u["user_id"]] for u in users]
        
    # Update slots
    elif "update slots set" in query_lower:
        slot_id = params[-1]
        if len(params) >= 4:
            chat_id = params[0]
            name = params[1]
            link = params[2]
        else:
            chat_id = params[0] if len(params) > 1 else ""
            name = f"Channel {slot_id}"
            link = params[0] if len(params) > 1 else ""
            
        slots_col.update_one(
            {"id": int(slot_id)}, 
            {"$set": {"chat_id": str(chat_id), "name": str(name), "link": str(link)}},
            upsert=True
        )
        return True
        
    return None
