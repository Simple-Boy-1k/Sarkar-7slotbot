import sqlite3

def init_db():
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS slots (id INTEGER PRIMARY KEY, chat_id TEXT, name TEXT, link TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    
    for i in range(1, 8):
        cur.execute("INSERT OR IGNORE INTO slots (id, chat_id, name, link) VALUES (?, '', '', '')", (i,))
    
    conn.commit()
    conn.close()

def get_db(sql, params=(), one=False, commit=False):
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute(sql, params)
    if commit:
        conn.commit()
        res = True
    else:
        res = cur.fetchone() if one else cur.fetchall()
    conn.close()
    return res

def get_setting(key, default=None):
    res = get_db("SELECT val FROM settings WHERE key=?", (key,), one=True)
    return res[0] if res else default

def set_setting(key, val):
    if val is None:
        get_db("DELETE FROM settings WHERE key=?", (key,), commit=True)
    else:
        get_db("INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)", (key, str(val)), commit=True)

def is_owner(user_id, owner_id):
    return user_id == owner_id

def is_admin(user_id, owner_id):
    if is_owner(user_id, owner_id):
        return True
    res = get_db("SELECT user_id FROM admins WHERE user_id=?", (user_id,), one=True)
    return bool(res)

