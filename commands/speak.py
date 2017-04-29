from datetime import datetime

import re
import pytz

from command import CommandRegistry, split_arguments
from commands import core
from commands.admin import _check_admin_group
from commands.db import _open_db_conn
from little_shit import get_target, check_target

__registry__ = cr = CommandRegistry()
__target_prefix = {'group': 'group_id','discuss': 'discuss_id','private': 'sender_id'}


@check_target
def speak_record(_, ctx_msg):
    target = get_target(ctx_msg)
    date = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
    time_text = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%H:%M')
    timemark_unix = int(datetime.now(tz=pytz.timezone('Asia/Shanghai')).timestamp())
    sender_id = ctx_msg.get('sender_id')
    sender_name = ctx_msg.get('sender_name')
    message = ctx_msg.get('content')
    text = message
    text = do_wash(text,wash_list('',ctx_msg,internal=True))
    cnt = len(text)
    if not target:
        return
    try:
        conn = _open_db_conn()
        conn.execute('INSERT INTO speak (target,sender_id,sender_name,date,time,timemark,message,text,charcount) VALUES (?,?,?,?,?,?,?,?,?)',
                     (target,sender_id,sender_name,date,time_text,timemark_unix,message,text,cnt))
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

def do_wash(text,washlist):
    for wash in washlist:
        w = wash.split(' , ')
        p = re.compile(r'' + w[0])
        text = p.sub(r'' + w[1],text)
    return text

@cr.register('wash')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def wash(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.wash <rule-for-wash>,<replace-to-wash>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    rule = argv[0]
    replace = argv[1]
    conn = _open_db_conn()
    conn.execute('INSERT INTO speak_wash (rule,replace) VALUES (?,?)', (rule,replace))
    conn.commit()
    conn.close()
    core.echo('成功添加清洗规则 ' + rule + ' -> ' + replace, ctx_msg)


@cr.register('wash_list', 'wash-list')
@cr.restrict(full_command_only=True, superuser_only=True)
def wash_list(_, ctx_msg, internal=False):
    if not internal:
        _check_admin_group(ctx_msg)
    conn = _open_db_conn()
    cursor = conn.execute('SELECT rule,replace FROM speak_wash')
    result = list(set([x[0] + ' , ' + x[1] for x in list(cursor)]))  # Get targets and remove duplications
    conn.close()
    if internal:
        return result
    if result:
        core.echo('已有清洗规则：\n' + '\n'.join(result), ctx_msg)
    else:
        core.echo('尚未有清洗规则设置', ctx_msg)


@cr.register('unwash')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def unwash(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.unwash <rule-for-wash>,<replace-to-wash>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    rule = argv[0]
    replace = argv[1]
    conn = _open_db_conn()
    conn.execute('DELETE FROM speak_wash WHERE rule = ? and replace=?', (rule,replace))
    conn.commit()
    conn.close()
    core.echo('成功取消清洗规则 ' + rule + ' -> ' + replace, ctx_msg)

@cr.register('query_today', 'query-today')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def query_today(_,ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.query_today <nick|qq>,<group_id>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    result=_query(ctx_msg,user=argv[0],group=argv[1])
    core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] ' + argv[0].replace('@', '', 1) + '今天在[' + str(argv[1])
              + ']共发言:' + str(result[0]) + ',有效发言:' + str(result[1]), ctx_msg)


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

@cr.register('total_today', 'total-today')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def total_today(_,ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.total_today <group_id>', ctx_msg)

    if len(argv) != 1:
        _send_error_msg()
        return

    date = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
    group = argv[0]
    if group == None:
        group = get_target(ctx_msg)
    else:
        new_ctx = ctx_msg.copy()
        new_ctx['group_id']=group
        new_ctx['group_tid'] = group
        group = get_target(new_ctx)

    conn = _open_db_conn()
    cursor = conn.execute("SELECT SUM(1) AS fullcount ,"
                          "SUM("
                          " CASE WHEN CAST(charcount AS INT) >= ("
                          "     SELECT CAST(param_value AS INT) "
                          "     FROM sys_params WHERE param_name='baseline') "
                          " THEN 1 ELSE 0 END) AS validcount "
                          "FROM speak WHERE target=? AND date=? ",
                          (group, date))
    result = cursor.fetchone()
    conn.close()
    if result[0] == None:
        result = (0,0)

    core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']今天共发言:' + str(result[0]) + ',有效发言:' + str(result[1]), ctx_msg)

@cr.register('top_today', 'top-today')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def top_today(_,ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.top_today <group_id>,<count>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    date = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
    group = argv[0]
    count = argv[1]
    if group == None:
        group = get_target(ctx_msg)
    else:
        new_ctx = ctx_msg.copy()
        new_ctx['group_id']=group
        new_ctx['group_tid'] = group
        group = get_target(new_ctx)

    conn = _open_db_conn()
    cursor = conn.execute("SELECT sender_id,sender_name,COUNT(1) AS cnt "
                          "FROM speak WHERE target=? AND date=? "
                          "GROUP BY target,sender_id,sender_name ORDER BY cnt DESC LIMIT " + str(count),
                          (group, date))
    result = ''
    for x in cursor:
        result = result + x[0] + '(' + x[1] + '):' + str(x[2]) + '\n'
    conn.close()

    core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']今天发言前' + str(count) +':\n' + result, ctx_msg)

@cr.register('vaildtop_today', 'vaildtop-today')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def vaildtop_today(_,ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.vaildtop_today <group_id>,<count>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    date = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
    group = argv[0]
    count = argv[1]
    if group == None:
        group = get_target(ctx_msg)
    else:
        new_ctx = ctx_msg.copy()
        new_ctx['group_id']=group
        new_ctx['group_tid'] = group
        group = get_target(new_ctx)

    conn = _open_db_conn()
    cursor = conn.execute("SELECT sender_id,sender_name,COUNT(1) AS cnt "
                          "FROM speak WHERE target=? AND date=? AND CAST(charcount AS INT) >= "
                          "(SELECT CAST(param_value AS INT) FROM sys_params WHERE param_name='baseline') "
                          "GROUP BY target,sender_id,sender_name ORDER BY cnt DESC LIMIT " + str(count),
                          (group, date))
    result = ''
    for x in cursor:
        result = result + x[0] + '(' + x[1] + '):' + str(x[2]) + '\n'
    conn.close()

    core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']今天有效发言前' + str(count) +':\n' + result, ctx_msg)
