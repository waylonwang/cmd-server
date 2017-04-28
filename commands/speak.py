import os
import sqlite3
from datetime import datetime
from commands.admin import _exchange_ctx_msg,_check_admin_group

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
    # conn.execute("""CREATE TABLE IF NOT EXISTS sys_params (
    #     pkey TEXT PRIMARY KEY NOT NULL,
    #     pvalue TEXT NOT NULL
    #     )""")
    # conn.execute("""INSERT INTO sys_params (pkey,pvalue)
    #     SELECT 'baseline','6' WHERE NOT EXISTS (
    #         SELECT 1 FROM sys_params WHERE pkey = 'baseline'
    #         )""")
    # conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_sys_params ON sys_params(target,key)""")
    conn.commit()
    return conn

@check_target
def speak_record(_, ctx_msg):
    target = get_target(ctx_msg)
    date = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
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
                     (target,sender_id,sender_name,date,time_text,timemark_unix,message,cnt))
        conn.commit()
    finally:
        conn.close()

@cr.register('查询发言')
@split_arguments(maxsplit=1)
@check_target
def speak_query(_,ctx_msg, argv=None):
    if len(argv) == 0 :
        user = None
        utext = '你'
    else:
        user = argv[0]
        utext = user.replace('@', '', 1)
    result=_query(ctx_msg,user=user)
    core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] ' + utext + '今天共发言:' + str(result[0])
      + ',有效发言:' + str(result[1]), ctx_msg)

@cr.register('query_today', 'query-today')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def query_today(_,ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.query_today <nick|qq>,<group_id>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    result=_query(ctx_msg,user=argv[0],group=argv[1])
    core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] ' + argv[0].replace('@', '', 1) + '今天在' + str(argv[1])
              + '共发言:' + str(result[0]) + ',有效发言:' + str(result[1]), ctx_msg)


def _query(ctx_msg,user=None,group=None,date=None):
    # ctx_msg = _exchange_ctx_msg(ctx_msg, 'in')

    if date == None:
        date = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')

    if group == None:
        group = get_target(ctx_msg)
    else:
        new_ctx = ctx_msg.copy()
        new_ctx['group_id']=group
        new_ctx['group_tid'] = group
        group = get_target(new_ctx)

    if user == None:
        user = ctx_msg.get('sender_id', '')
    else:
        user = user.replace('@','',1)

    conn = _open_db_conn()
    cursor = conn.execute("SELECT SUM(1) AS fullcount ,"
                          "SUM("
                          " CASE WHEN CAST(charcount AS INT) >= ("
                          "     SELECT CAST(param_value AS INT) "
                          "     FROM sys_params WHERE param_name='baseline') "
                          " THEN 1 ELSE 0 END) AS validcount "
                          "FROM speak WHERE target=? AND (sender_id=? OR sender_name=?) AND date=? ",
                          (group, user, user, date))
    result = cursor.fetchone()
    conn.close()
    if result[0] == None:
        result = (0,0)
    return result