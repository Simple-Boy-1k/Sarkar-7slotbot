import os
from pymongo import MongoClient

# Aapka MongoDB Atlas Link seedha add kar diya gaya hai
MONGO_URI = os.getenv("MONGO_URI") or "mongodb+srv://sksahnawaj89_db_user:4TjZxb4Xfz0O0TNr@cluster0.5raayqr.mongodb.net/?appName=Cluster0"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["telegram_bot_db"]

settings_col = db["settings"]
slots_col = db["slots"]
users_col = db["users"]
admins_col = db["admins"]

def init_db():
    """main.py ke initialization ke liye"""
    if slots_col.count_documents({}) == 0:
        for i in range(1, 8):
            slots_col.insert_one({"id": i, "chat_id": "", "name": f"Channel {i}", "link": ""})

def set_setting(key, value):
    settings_col.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

def get_setting(key):
    res = settings_col.find_one({"key": key})
    return res["value"] if res else ""

def is_admin(user_id: int, owner_id: int = None) -> bool:
    """main.py ke admin check ke liye"""
    if owner_id and user_id == owner_id:
        return True
    admin = admins_col.find_one({"user_id": user_id})
    return bool(admin)

def get_db(query, params=(), commit=False):
    query_lower = str(query).strip().lower()
    
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

# Database initialize
init_db()
