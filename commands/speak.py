import os
import sqlite3
from datetime import datetime
from commands.scope import exchange_ctx_msg

import pytz

from command import CommandRegistry, split_arguments
from commands import core
from config import config
from interactive import *
from little_shit import get_db_dir, get_source, get_target, check_target

__registry__ = cr = CommandRegistry()
__target_prefix = {'group': 'group_id','discuss': 'discuss_id','private': 'sender_id'}

def _open_db_conn():
    conn = sqlite3.connect(os.path.join(get_db_dir(), 'score.sqlite'))
    conn.execute("""CREATE TABLE IF NOT EXISTS speak (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        target TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        timemark INTEGER NOT NULL,
        message TEXT NOT NULL,
        charcount NOT NULL
        )""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speak_sender ON speak(sender_id)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speak_date ON speak(date)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speak_charcount ON speak(charcount)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS speak_count (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        target TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        date TEXT NOT NULL,
        fullcount INTEGER NOT NULL,
        rulecount INTEGER NOT NULL
        )""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speakcount_sender ON speak_count(sender_id)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speakcount_date ON speak_count(date)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speakcount_fullcount ON speak_count(fullcount)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_speakcount_rulecount ON speak_count(rulecount)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS speak_param (
        pkey TEXT PRIMARY KEY NOT NULL,
        pvalue TEXT NOT NULL
        )""")
    conn.execute("""INSERT INTO speak_param (pkey,pvalue) 
        SELECT 'baseline','6' WHERE NOT EXISTS (
            SELECT 1 FROM speak_param WHERE pkey = 'baseline'
            )""")
    # conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_speak_param ON speak_param(target,key)""")
    conn.commit()
    return conn

@check_target
def speak_record(_, ctx_msg):
    target = get_target(ctx_msg)
    date_text = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
    time_text = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%H:%M')
    timemark_unix = int(datetime.now(tz=pytz.timezone('Asia/Shanghai')).timestamp())
    sender_id = ctx_msg.get('sender_id')
    sender_name = ctx_msg.get('sender_name')
    message = ctx_msg.get('content')
    cnt = len(ctx_msg.get('text'))
    if not target:
        return
    try:
        conn = _open_db_conn()
        conn.execute('INSERT INTO speak (target,sender_id,sender_name,date,time,timemark,message,charcount) VALUES (?,?,?,?,?,?,?,?)',
                     (target,sender_id,sender_name,date_text,time_text,timemark_unix,message,cnt))
        conn.commit()
    finally:
        conn.close()

@cr.register('查询发言')
@split_arguments(maxsplit=1)
@check_target
def speak_query(_,ctx_msg, argv=None):
    ctx_msg = exchange_ctx_msg(ctx_msg, 'in')
    date_text = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
    conn = _open_db_conn()
    if len(argv) == 0 :
        cursor = conn.execute("SELECT count(id) FROM speak where target=? and sender_id=? and date=? "
                              "and charcount> (select cast(pvalue as int) from speak_param where pkey='baseline')",
                              (get_target(ctx_msg), ctx_msg.get('sender_id', ''), date_text))
        rule_cnt = cursor.fetchone()[0]
        cursor = conn.execute('SELECT count(id) FROM speak where target=? and sender_id=? and date=?',
                              (get_target(ctx_msg), ctx_msg.get('sender_id', ''), date_text))
        today_cnt = cursor.fetchone()[0]
        conn.close()
        core.echo('[CQ:at,qq='+ ctx_msg.get('sender_id')+'] 你今天共发言:' + str(today_cnt)
                  + ',有效发言:'+ str(rule_cnt), ctx_msg)
    else:
        cursor = conn.execute("SELECT count(id) FROM speak where target=? and sender_name=? and date=? "
                              "and charcount> (select cast(pvalue as int) from speak_param where pkey='baseline')",
                              (get_target(ctx_msg), argv[0].replace('@','',1), date_text))
        rule_cnt = cursor.fetchone()[0]
        cursor = conn.execute('SELECT count(id) FROM speak where target=? and sender_name=? and date=?',
                              (get_target(ctx_msg), argv[0].replace('@','',1), date_text))
        today_cnt = cursor.fetchone()[0]
        conn.close()
        core.echo('[CQ:at,qq='+ ctx_msg.get('sender_id')+'] '+ argv[0].replace('@','',1) + '今天共发言:'
                  + str(today_cnt) + ',有效发言:'+ str(rule_cnt), ctx_msg)

@cr.register('set_baseline','set-baseline')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
@split_arguments(maxsplit=1)
def set_baseline(_, ctx_msg, argv=None):
    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.set_baseline <value>', ctx_msg)

    if len(argv) != 1:
        _send_error_msg()
        return

    value=argv[0]
    conn = _open_db_conn()
    conn.execute('INSERT OR REPLACE INTO speak_param (pkey,pvalue) VALUES (?,?)', ('baseline',argv[0]))
    conn.commit()
    conn.close()
    core.echo('成功设置最低发言数:' + value, ctx_msg)


@cr.register('baseline')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
def baseline(_, ctx_msg, internal=False):
    conn = _open_db_conn()
    cursor = conn.execute("SELECT pvalue FROM speak_param where pkey='baseline'")
    result = list(set([x[0] for x in list(cursor)]))  # Get targets and remove duplications
    conn.close()
    if internal:
        return result
    if result:
        core.echo('最低发言数:'+','.join(result), ctx_msg)
    else:
        core.echo('尚未有最低发言数设置', ctx_msg)
