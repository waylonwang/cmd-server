from command import CommandRegistry, CommandScopeError, split_arguments
from commands import core
from commands.db import _open_db_conn
from little_shit import get_target,get_source
from interactive import *

__registry__ = cr = CommandRegistry()

__target_prefix = {'group': 'group_id', 'discuss': 'discuss_id', 'private': 'sender_id'}

_cmd_help = 'admin.help'

@cr.register('test')
@cr.restrict(full_command_only=True, superuser_only=True)
def test(_, ctx_msg):
    core.echo('Your are the superuser!', ctx_msg)


@cr.register('help')
@cr.restrict(full_command_only=True, superuser_only=True)
def help(args_text, ctx_msg,allow_interactive=True):
    _check_admin_group(ctx_msg)

    source = get_source(ctx_msg)
    if allow_interactive and (not args_text or has_session(source, _cmd_help)):
        # Be interactive
        return _help_interactively(args_text, ctx_msg, source)

    if args_text== '1':
        core.echo(
            '(1)设置系统参数：admin.set_param \n<name>,<value>\n'
            '(2)查询系统参数：admin.get_param \n<name>'
            , ctx_msg
        )
    elif args_text == '2':
        core.echo(
            '(1)设置白名单：admin.allow \ngroup|discuss|private,<account-to-block>\n'
            '(2)设置黑名单：admin.block \ngroup|discuss|private,<account-to-block>\n'
            '(3)取消白名单：admin.unallow \ngroup|discuss|private,<account-to-block>\n'
            '(4)取消黑名单：admin.unblock \ngroup|discuss|private,<account-to-block>\n'
            '(5)查询白名单：admin.allow_list\n'
            '(6)查询黑名单：admin.block_list'
            # '(7)设置交换名单：admin.exchange \nin|out,<account-orig>,<account-dest>\n'
            # '(8)取消交换名单：admin.unexchange \nin|out,<account-orig>,<account-dest>\n'
            # '(9)查询交换名单：admin.exchange_list\n'
            , ctx_msg
        )
    elif args_text == '3':
        core.echo(
            '(1)设置发言清洗规则：speak.wash \n<rule-for-wash>,<replace-to-wash>\n'
            '(2)取消发言清洗规则：speak.unwash \n<rule-for-wash>,<replace-to-wash>\n'
            '(3)查询发言清洗规则：speak.wash_list'
            , ctx_msg
        )
    elif args_text == '4':
        core.echo(
            '(1)查询群成员发言数：speak.query \n<nick|qq>,<group_id>,<YYYY-MM-DD>\n'
            '(2)查询群发言总数：speak.total \n<group_id>,<YYYY-MM-DD>\n'
            '(3)查询群发言Top X：speak.top \n<group_id>,<count>,<YYYY-MM-DD>\n'
            '(4)查询群有效发言Top X：speak.vaildtop \n<group_id>,<count>,<YYYY-MM-DD>\n'
            '(5)更新群有效发言数据：speak.updatewash <group_id>,<YYYY-MM-DD>\n'
            , ctx_msg
        )
    else:
        core.echo(
            '不支持此指令参数，请重新发起命令'
            , ctx_msg
        )

_state_machines = {}

def _help_interactively(args_text, ctx_msg, source):
    def wait_for_type(s, a, c):
        core.echo('你好，超级管理员！请输入你要查找的命令类型：\n'
                  '[1]:基础系统命令\n'
                  '[2]:拦截放行命令\n'
                  '[3]:发言设置命令'
                  '[4]:发言管理命令'
                  , c)
        s.state += 1

    def show_guide(s, a, c):
        help(a, c, allow_interactive=False)
        return True

    if _cmd_help not in _state_machines:
        _state_machines[_cmd_help] = (
            wait_for_type,  # 0
            show_guide  # 1
        )

    sess = get_session(source, _cmd_help)
    if _state_machines[_cmd_help][sess.state](sess, args_text, ctx_msg):
        # Done
        remove_session(source, _cmd_help)

@cr.register('block')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def block(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.block group|discuss|private,<account-to-block>', ctx_msg)

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
@cr.restrict(full_command_only=True, superuser_only=True)
def block_list(_, ctx_msg, internal=False):
    if not internal:
        _check_admin_group(ctx_msg)
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
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def unblock(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.unblock group|discuss|private,<account-to-unblock>', ctx_msg)

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
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def allow(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.allow group|discuss|private,<account-to-allow>', ctx_msg)

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
@cr.restrict(full_command_only=True, superuser_only=True)
def allow_list(_, ctx_msg, internal=False):
    if not internal:
        _check_admin_group(ctx_msg)
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
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def unallow(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.unallow group|discuss|private,<account-to-unallow>', ctx_msg)

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


# @cr.register('exchange')
# @cr.restrict(full_command_only=True, superuser_only=True)
# @split_arguments(maxsplit=3)
# def exchange(_, ctx_msg, argv=None):
#     _check_admin_group(ctx_msg)
#
#     def _send_error_msg():
#         core.echo('参数不正确。\n\n正确使用方法：\nadmin.exchange in|out,<account-orig>,<account-dest>', ctx_msg)
#
#     if len(argv) != 3:
#         _send_error_msg()
#         return
#
#     direction = argv[0]
#     orig = argv[1]
#     dest = argv[2]
#
#     conn = _open_db_conn()
#     conn.execute('INSERT OR IGNORE INTO exchange_group_list (direction,orig,dest) VALUES (?,?,?)',
#                  (direction, orig, dest))
#     conn.commit()
#     conn.close()
#     core.echo('成功交换 ' + direction + ':from ' + orig + ' to ' + dest, ctx_msg)
#

# @cr.register('exchange_list', 'exchange-list')
# @cr.restrict(full_command_only=True, superuser_only=True)
# def exchange_list(_, ctx_msg, internal=False):
#     if not internal:
#         _check_admin_group(ctx_msg)
#     conn = _open_db_conn()
#     cursor = conn.execute('SELECT direction,orig,dest FROM exchange_group_list')
#     exchange_list = list(
#         set([x[0] + ':' + x[1] + '->' + x[2] for x in list(cursor)]))  # Get targets and remove duplications
#     conn.close()
#     if internal:
#         return exchange_list
#     if exchange_list:
#         core.echo('已交换：\n' + ', '.join(exchange_list), ctx_msg)
#     else:
#         core.echo('尚未有交换设置', ctx_msg)
#
#
# @cr.register('unexchange')
# @cr.restrict(full_command_only=True, superuser_only=True)
# @split_arguments(maxsplit=3)
# def unexchange(_, ctx_msg, argv=None):
#     _check_admin_group(ctx_msg)
#
#     def _send_error_msg():
#         core.echo('参数不正确。\n\n正确使用方法：\nadmin.unexchange in|out,<account-orig>,<account-dest>', ctx_msg)
#
#     if len(argv) != 3:
#         _send_error_msg()
#         return
#
#     direction = argv[0]
#     orig = argv[1]
#     dest = argv[2]
#
#     conn = _open_db_conn()
#     conn.execute('DELETE FROM exchange_group_list WHERE direction = ? and orig=? and dest=?', (direction, orig, dest))
#     conn.commit()
#     conn.close()
#     core.echo('成功取消交换 ' + direction + ':from ' + orig + ' to ' + dest, ctx_msg)
#
#
# def _exchange_ctx_msg(ctx_msg, direction):
#     orig = ctx_msg.get('group_id', '')
#     conn = _open_db_conn()
#     cursor = conn.execute('SELECT dest FROM exchange_group_list where direction=? and orig=?', (direction, orig))
#     if cursor.rowcount > 0:
#         dest = cursor.fetchone()[0]
#     else:
#         dest = None
#     conn.close()
#     if dest != None:
#         ctx_msg['group_id'] = dest
#         ctx_msg['group_tid'] = dest
#         ctx_msg['raw_ctx']['group_id'] = dest
#     return ctx_msg


@cr.register('set_param', 'set-param')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=2)
def set_param(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.set_param <name>,<value>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    name = argv[0]
    value = argv[1]
    conn = _open_db_conn()
    conn.execute('INSERT OR REPLACE INTO sys_params (param_name,param_value) VALUES (?,?)', (name, value))
    conn.commit()
    conn.close()
    core.echo('成功设置系统参数' + name + ':' + value, ctx_msg)


@cr.register('get_param', 'get-param')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def get_param(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.get_param <name>', ctx_msg)

    if len(argv) != 1:
        _send_error_msg()
        return
    result = _read_param(ctx_msg, argv[0])
    if result:
        core.echo('系统参数' + argv[0] + ':' + str(result), ctx_msg)
    else:
        core.echo('尚未有设置该系统参数', ctx_msg)


def _read_param(ctx_msg, argv=None):
    name = argv
    conn = _open_db_conn()
    cursor = conn.execute('SELECT param_value FROM sys_params where param_name=?', (name,))
    try:
        result = cursor.fetchone()[0]
    except:
        result = None
    finally:
        conn.close()
    return result


def _check_admin_group(ctx_msg):
    if ctx_msg.get('msg_type','') == 'group':
        if _read_param(ctx_msg, 'admin_group') != ctx_msg.get('group_id', ''):
            # core.echo('此命令只能在管理组中使用', ctx_msg)
            raise CommandScopeError('非管理组')

