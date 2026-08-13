import os
from pymongo import MongoClient

# MongoDB Connection Link (Environment variable se ya direct fallback)
MONGO_URI = os.getenv("MONGO_URI") or "mongodb+srv://sksahnawaj89_db_user:4TjZxb4Xfz0O0TNr@cluster0.5raayqr.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["telegram_bot_db"]

settings_col = db["settings"]
slots_col = db["slots"]
users_col = db["users"]
admins_col = db["admins"]

def init_db():
    """Database initialize karta hai agar slots nahi hain"""
    if slots_col.count_documents({}) == 0:
        for i in range(1, 8):
            slots_col.insert_one({"id": i, "chat_id": "", "name": f"Channel {i}", "link": ""})

def set_setting(key, value):
    """Setting update ya insert karta hai"""
    settings_col.update_one({"key": key}, {"$set": {"value": str(value)}}, upsert=True)

def get_setting(key):
    """Setting value fetch karta hai"""
    res = settings_col.find_one({"key": key})
    return res["value"] if res and "value" in res else ""

def is_admin(user_id: int, owner_id: int = None) -> bool:
    """Admin status check karta hai"""
    if owner_id and int(user_id) == int(owner_id):
        return True
    admin = admins_col.find_one({"user_id": int(user_id)})
    return bool(admin)

def get_db(query, params=(), commit=False):
    """SQL Queries ko MongoDB functions mein Map karta hai"""
    query_lower = str(query).strip().lower()
    
    # User Registration
    if "insert" in query_lower and "users" in query_lower:
        if params:
            u_id = int(params[0])
            users_col.update_one({"user_id": u_id}, {"$set": {"user_id": u_id}}, upsert=True)
        return True

    # User Count
    elif "count(*)" in query_lower and "users" in query_lower:
        count = users_col.count_documents({})
        return [[count]]
        
    # Get All Users List
    elif "select user_id from users" in query_lower:
        users = users_col.find({}, {"user_id": 1})
        return [[u["user_id"]] for u in users]

    # Handle Slots Queries (Read & Update)
    elif "slots" in query_lower:
        if "update" in query_lower:
            slot_id = params[-1]
            chat_id = str(params[0]) if len(params) > 0 else ""
            name = str(params[1]) if len(params) > 1 else f"Channel {slot_id}"
            link = str(params[2]) if len(params) > 2 else ""
            slots_col.update_one(
                {"id": int(slot_id)}, 
                {"$set": {"chat_id": chat_id, "name": name, "link": link}},
                upsert=True
            )
            return True
        else:
            # Query for slots fetch
            slots = list(slots_col.find().sort("id", 1))
            if "chat_id" in query_lower:
                # Returns 4 items: id, chat_id, name, link
                return [[s["id"], str(s.get("chat_id", "")), str(s.get("name", "")), str(s.get("link", ""))] for s in slots]
            else:
                # Returns 3 items: id, name, link
                return [[s["id"], str(s.get("name", "")), str(s.get("link", ""))] for s in slots]

    return []

# Auto initialize
init_db()
