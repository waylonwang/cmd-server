import os
import sqlite3

from little_shit import get_db_dir

def _open_db_conn():
    conn = sqlite3.connect(os.path.join(get_db_dir(), 'score.sqlite'))
    __create_table(conn)
    __create_index(conn)
    __init_data(conn)
    conn.commit()
    return conn

def __create_table(conn):
    # base table
    conn.execute("""CREATE TABLE IF NOT EXISTS sys_params (
        param_name TEXT PRIMARY KEY NOT NULL,
        param_value TEXT NOT NULL
        )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS group_member_info (
        group_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        nickname TEXT,
        card TEXT,
        sex TEXT,
        age INTEGER,
        area TEXT,
        join_time INTEGER,
        last_sent_time INTEGER,
        level TEXT,
        role TEXT,
        unfriendly INTEGER,
        title TEXT,
        title_expire_time INTEGER,
        card_changeable INTEGER,
        updatetime INTEGER
        )""")
    # admin table
    conn.execute("""CREATE TABLE IF NOT EXISTS allowed_target_list (
        target TEXT NOT NULL
        )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS blocked_target_list (
        target TEXT NOT NULL
        )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS exchange_group_list (
        direction TEXT NOT NULL,
        orig TEXT NOT NULL,
        dest TEXT NOT NULL
        )""")
    # speak table
    conn.execute("""CREATE TABLE IF NOT EXISTS speak (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        target TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        timemark INTEGER NOT NULL,
        message TEXT NOT NULL,
        text TEXT NOT NULL,
        charcount NOT NULL
        )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS speak_count (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        target TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        date TEXT NOT NULL,
        fullcount INTEGER NOT NULL,
        rulecount INTEGER NOT NULL
        )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS speak_wash (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        rule TEXT NOT NULL,
        replace TEXT NOT NULL
        )""")

def __create_index(conn):
    conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_exchange_all ON exchange_group_list(direction,orig,dest)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speak_sender ON speak(sender_id)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speak_date ON speak(date)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speak_charcount ON speak(charcount)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speakcount_sender ON speak_count(sender_id)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speakcount_date ON speak_count(date)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speakcount_fullcount ON speak_count(fullcount)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speakcount_rulecount ON speak_count(rulecount)""")

def __init_data(conn):
    conn.execute("""INSERT INTO allowed_target_list (target) 
        SELECT 'g#*' WHERE NOT EXISTS (
            SELECT 1 FROM allowed_target_list WHERE target LIKE 'g#%'
            )""")
    conn.execute("""INSERT INTO allowed_target_list (target) 
        SELECT 'd#*' WHERE NOT EXISTS (
            SELECT 1 FROM allowed_target_list WHERE target LIKE 'd#%'
            )""")
    conn.execute("""INSERT INTO allowed_target_list (target) 
        SELECT 'p#*' WHERE NOT EXISTS (
            SELECT 1 FROM allowed_target_list WHERE target LIKE 'p#%'
            )""")
    conn.execute("""INSERT INTO sys_params (param_name,param_value) 
        SELECT 'baseline','6' WHERE NOT EXISTS (
            SELECT 1 FROM sys_params WHERE param_name = 'baseline'
            )""")
