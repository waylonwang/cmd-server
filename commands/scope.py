import os
import sqlite3

from command import CommandRegistry, split_arguments
from commands import core
from little_shit import get_db_dir, get_default_db_path, get_target

__registry__ = cr = CommandRegistry()

__target_prefix = {'group': 'group_id','discuss': 'discuss_id','private': 'sender_id'}


def _open_db_conn():
    conn = sqlite3.connect(os.path.join(get_db_dir(), 'score.sqlite'))
    conn.execute("""CREATE TABLE IF NOT EXISTS allowed_target_list (
        target TEXT NOT NULL
        )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS blocked_target_list (
        target TEXT NOT NULL
        )""")
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
    conn.execute("""CREATE TABLE IF NOT EXISTS exchange_group_list (
        direction TEXT NOT NULL,
        orig TEXT NOT NULL,
        dest TEXT NOT NULL
        )""")
    conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_exchange_all ON exchange_group_list(direction,orig,dest)""")
    conn.commit()
    return conn


@cr.register('test')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
def test(_, ctx_msg):
    core.echo('Your are the superuser!', ctx_msg)


@cr.register('block')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
@split_arguments(maxsplit=2)
def block(_, ctx_msg, argv=None):
    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nscope.block group|discuss|private,<account-to-block>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    type = argv[0]
    account = argv[1]
    # Get a target using a fake context message
    target = get_target({
        'via': 'default',
        'msg_type': type,
        __target_prefix.get(type): account
    })

    if not target:
        _send_error_msg()
        return

    conn = _open_db_conn()
    conn.execute('INSERT INTO blocked_target_list (target) VALUES (?)', (target,))
    conn.commit()
    conn.close()
    core.echo('成功屏蔽 ' + type + ':' + account, ctx_msg)


@cr.register('block_list', 'block-list')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
def block_list(_, ctx_msg, internal=False):
    conn = _open_db_conn()
    cursor = conn.execute('SELECT target FROM blocked_target_list')
    blocked_targets = list(set([x[0] for x in list(cursor)]))  # Get targets and remove duplications
    conn.close()
    if internal:
        return blocked_targets
    if blocked_targets:
        core.echo('已屏蔽：\n' + ', '.join(blocked_targets), ctx_msg)
    else:
        core.echo('尚未有屏蔽设置', ctx_msg)


@cr.register('unblock')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
@split_arguments(maxsplit=2)
def unblock(_, ctx_msg, argv=None):
    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nscope.unblock group|discuss|private,<account-to-unblock>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    type = argv[0]
    account = argv[1]
    # Get a target using a fake context message
    target = get_target({
        'via': 'default',
        'msg_type': type,
        __target_prefix.get(type): account
    })

    if not target:
        _send_error_msg()
        return

    conn = _open_db_conn()
    conn.execute('DELETE FROM blocked_target_list WHERE target = ?', (target,))
    conn.commit()
    conn.close()
    core.echo('成功取消屏蔽 ' + type + ':' + account, ctx_msg)

@cr.register('allow')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
@split_arguments(maxsplit=2)
def allow(_, ctx_msg, argv=None):
    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nscope.allow group|discuss|private,<account-to-allow>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    type = argv[0]
    account = argv[1]
    # Get a target using a fake context message
    target = get_target({
        'via': 'default',
        'msg_type': type,
        __target_prefix.get(type): account
    })

    if not target:
        _send_error_msg()
        return

    conn = _open_db_conn()
    conn.execute('INSERT INTO allowed_target_list (target) VALUES (?)', (target,))
    conn.commit()
    conn.close()
    core.echo('成功允许 ' + type + ':' + account, ctx_msg)


@cr.register('allow_list', 'allow-list')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=True)
def allow_list(_, ctx_msg, internal=False):
    conn = _open_db_conn()
    cursor = conn.execute('SELECT target FROM allowed_target_list')
    allowed_targets = list(set([x[0] for x in list(cursor)]))  # Get targets and remove duplications
    conn.close()
    if internal:
        return allowed_targets
    if allowed_targets:
        core.echo('已允许：\n' + ', '.join(allowed_targets), ctx_msg)
    else:
        core.echo('尚未有允许设置', ctx_msg)


@cr.register('unallow')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
@split_arguments(maxsplit=2)
def unallow(_, ctx_msg, argv=None):
    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nscope.unallow group|discuss|private,<account-to-unallow>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    type = argv[0]
    account = argv[1]
    # Get a target using a fake context message
    target = get_target({
        'via': 'default',
        'msg_type': type,
        __target_prefix.get(type): account
    })

    if not target:
        _send_error_msg()
        return

    conn = _open_db_conn()
    conn.execute('DELETE FROM allowed_target_list WHERE target = ?', (target,))
    conn.commit()
    conn.close()
    core.echo('成功取消允许 ' + type + ':' + account, ctx_msg)

@cr.register('exchange')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
@split_arguments(maxsplit=3)
def exchange(_, ctx_msg, argv=None):
    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nscope.exchange in|out,<account-orig>,<account-dest>', ctx_msg)

    if len(argv) != 3:
        _send_error_msg()
        return

    direction = argv[0]
    orig = argv[1]
    dest = argv[2]

    conn = _open_db_conn()
    conn.execute('INSERT OR IGNORE INTO exchange_group_list (direction,orig,dest) VALUES (?,?,?)', (direction,orig,dest))
    conn.commit()
    conn.close()
    core.echo('成功交换 ' + direction + ':from ' + orig + ' to ' + dest, ctx_msg)


@cr.register('exchange_list', 'exchange-list')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=True)
def exchange_list(_, ctx_msg, internal=False):
    conn = _open_db_conn()
    cursor = conn.execute('SELECT direction,orig,dest FROM exchange_group_list')
    exchange_list = list(set([x[0]+':'+x[1]+'->'+x[2] for x in list(cursor)]))  # Get targets and remove duplications
    conn.close()
    if internal:
        return exchange_list
    if exchange_list:
        core.echo('已交换：\n' + ', '.join(exchange_list), ctx_msg)
    else:
        core.echo('尚未有交换设置', ctx_msg)


@cr.register('unexchange')
@cr.restrict(full_command_only=True, superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
@split_arguments(maxsplit=3)
def unexchange(_, ctx_msg, argv=None):
    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nscope.unexchange in|out,<account-orig>,<account-dest>', ctx_msg)

    if len(argv) != 3:
        _send_error_msg()
        return

    orig = argv[1]
    dest = argv[2]

    conn = _open_db_conn()
    conn.execute('DELETE FROM exchange_group_list WHERE direction = ? and orig=? and dest=?', (direction,orig,dest))
    conn.commit()
    conn.close()
    core.echo('成功取消交换 ' + direction + ':from ' + orig + ' to ' + dest, ctx_msg)

def exchange_ctx_msg(ctx_msg,direction):
    orig = ctx_msg.get('group_id', '')
    conn = _open_db_conn()
    cursor = conn.execute('SELECT dest FROM exchange_group_list where direction=? and orig=?',(direction,orig))
    if cursor.rowcount>0:
        dest = cursor.fetchone()[0]
    else:
        dest = None
    conn.close()
    if dest != None:
        ctx_msg['group_id'] = dest
        ctx_msg['group_tid'] = dest
        ctx_msg['raw_ctx']['group_id'] = dest
    return ctx_msg
