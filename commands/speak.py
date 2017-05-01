import re
from datetime import datetime

import pytz

from command import CommandRegistry, split_arguments
from commands import core
from commands.admin import _check_admin_group
from commands.db import _open_db_conn
from little_shit import get_target, check_target

__registry__ = cr = CommandRegistry()
__target_prefix = {'group': 'group_id', 'discuss': 'discuss_id', 'private': 'sender_id'}


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
    text = _do_wash(text, wash_list('', ctx_msg, internal=True))
    cnt = len(text)
    if not target:
        return
    try:
        conn = _open_db_conn()
        conn.execute(
            'INSERT INTO speak (target,sender_id,sender_name,date,time,timemark,message,text,charcount) VALUES (?,?,?,?,?,?,?,?,?)',
            (target, sender_id, sender_name, date, time_text, timemark_unix, message, text, cnt))
        conn.commit()
    finally:
        conn.close()


@cr.register('查询发言')
@split_arguments(maxsplit=1)
@check_target
def speak_query(_, ctx_msg, argv=None):
    if len(argv) == 0:
        user = None
        utext = '你'
    else:
        user = argv[0]
        utext = user.replace('@', '', 1)
    result = _queryspeak(ctx_msg, user=user)
    core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] ' + utext + '今天共发言:' + str(result[0])
              + ',有效发言:' + str(result[1]), ctx_msg)


def _do_wash(text, washlist):
    for wash in washlist:
        w = wash.split(' , ')
        p = re.compile(r'' + w[0])
        text = p.sub(r'' + w[1], text)
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
    conn.execute('INSERT INTO speak_wash (rule,replace) VALUES (?,?)', (rule, replace))
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
    conn.execute('DELETE FROM speak_wash WHERE rule = ? and replace=?', (rule, replace))
    conn.commit()
    conn.close()
    core.echo('成功取消清洗规则 ' + rule + ' -> ' + replace, ctx_msg)

@cr.register('updatewash')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def updatewash(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.updatewash <group_id>,<YYYY-MM-DD>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    group = argv[0]
    date = argv[1]
    new_ctx = ctx_msg.copy()
    new_ctx['group_id'] = group
    new_ctx['group_tid'] = group
    group = get_target(new_ctx)
    washlist=wash_list('', ctx_msg, internal=True)

    core.echo('即将开始更新' + date + '[' + argv[0] + ']' + '的发言数据，耗时可能较长，请耐心等候！', ctx_msg)
    conn = _open_db_conn()
    cursor = conn.execute('SELECT id,message FROM speak WHERE target = ? and date=?', (group, date))
    values = cursor.fetchall()
    total = len(values)
    print('共'+str(total))
    i=0
    for x in values:
        i= i+1
        print('当前'+str(i))
        id = x[0]
        message = x[1]
        text = _do_wash(message, washlist)
        cnt = len(text)
        conn.execute('UPDATE speak SET text = ?,charcount = ? WHERE id = ?', (text, cnt, id))
        conn.commit()
    conn.close()
    core.echo('成功更新'+ date + '[' + argv[0] + ']' + '有效发言数据', ctx_msg)


@cr.register('query', 'query')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=3)
def query(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.query <nick|qq>,<group_id>,<YYYY-MM-DD>', ctx_msg)

    if len(argv) != 3:
        _send_error_msg()
        return

    result = _queryspeak(ctx_msg, user=argv[0], group=argv[1], date = argv[2])
    core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] ' + argv[0].replace('@', '', 1) + ' ' + argv[2] + '在[' + str(argv[1])
              + ']共发言:' + str(result[0]) + ',有效发言:' + str(result[1]), ctx_msg)


def _queryspeak(ctx_msg, user=None, group=None, date=None):
    # ctx_msg = _exchange_ctx_msg(ctx_msg, 'in')

    if date == None:
        date = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')

    if group == None:
        group = get_target(ctx_msg)
    else:
        new_ctx = ctx_msg.copy()
        new_ctx['group_id'] = group
        new_ctx['group_tid'] = group
        group = get_target(new_ctx)

    if user == None:
        user = ctx_msg.get('sender_id', '')
    else:
        user = user.replace('@', '', 1)

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
        result = (0, 0)
    return result


@cr.register('total', 'total')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def total(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.total <group_id>,<YYYY-MM-DD>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    group = argv[0]
    date = argv[1]

    new_ctx = ctx_msg.copy()
    new_ctx['group_id'] = group
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
        result = (0, 0)

    core.echo(
        '[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']' +  date + '共发言:' + str(result[0]) + ',有效发言:' + str(
            result[1]), ctx_msg)


@cr.register('top', 'top')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=3)
def top(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.top <group_id>,<count>,<YYYY-MM-DD>', ctx_msg)

    if len(argv) != 3:
        _send_error_msg()
        return

    group = argv[0]
    count = argv[1]
    date = argv[2]

    new_ctx = ctx_msg.copy()
    new_ctx['group_id'] = group
    new_ctx['group_tid'] = group
    group = get_target(new_ctx)
    # TODO 排除sender_name，避免改名后数量不能合并计算，sender_name改为从缓存中取最新的显示
    conn = _open_db_conn()
    cursor = conn.execute("SELECT sender_id,sender_name,COUNT(1) AS cnt "
                          "FROM speak WHERE target=? AND date=? "
                          "GROUP BY target,sender_id,sender_name ORDER BY cnt DESC LIMIT ?" ,
                          (group, date, count))
    msg = '[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']' + date + '有效发言前' + str(count) + ':'
    i = 1
    msglist = []
    for x in cursor:
        msg = msg + '\n' + str(i) + '.' + x[1] + '(' + x[0] + '):' + str(x[2])
        if i % 5 == 0:
            msglist.append(msg)
            msg = '[CQ:at,qq=' + ctx_msg.get('sender_id') + ']'
        i = i + 1
    if (i-1) % 5 != 0:
        msglist.append(msg)
    conn.close()
    for k, v in enumerate(msglist):
        core.echo(v,ctx_msg)


@cr.register('vaildtop', 'vaildtop')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=3)
def vaildtop(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.vaildtop <group_id>,<count>,<YYYY-MM-DD>', ctx_msg)

    if len(argv) != 3:
        _send_error_msg()
        return

    group = argv[0]
    count = argv[1]
    date = argv[2]

    new_ctx = ctx_msg.copy()
    new_ctx['group_id'] = group
    new_ctx['group_tid'] = group
    group = get_target(new_ctx)

    conn = _open_db_conn()
    cursor = conn.execute("SELECT sender_id,sender_name,COUNT(1) AS cnt "
                          "FROM speak WHERE target=? AND date=? AND CAST(charcount AS INT) >= "
                          "(SELECT CAST(param_value AS INT) FROM sys_params WHERE param_name='baseline') "
                          "GROUP BY target,sender_id,sender_name ORDER BY cnt DESC LIMIT ?" ,
                          (group, date, count))
    msg = '[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']' + date + '有效发言前' + str(count) + ':'
    i = 1
    msglist = []
    for x in cursor:
        msg = msg + '\n' + str(i) + '.' + x[1] + '(' + x[0] + '):' + str(x[2])
        if i % 5 == 0:
            msglist.append(msg)
            msg = '[CQ:at,qq=' + ctx_msg.get('sender_id') + ']'
        i = i + 1
    if (i-1) % 5 != 0:
        msglist.append(msg)
    conn.close()
    for k, v in enumerate(msglist):
        core.echo(v,ctx_msg)