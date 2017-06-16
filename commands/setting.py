# -*- coding: utf-8 -*-
"""
    commands.setting
    ~~~~~~~~~~~~~~~~
    机器人设置的命令模块
"""

from biz_adapters.score_biz_server import ScoreBizAdapter
from command import CommandRegistry, CommandScopeError, CommandPermissionError, split_arguments
from commands import core
from config import config
from interactive import *
from little_shit import get_target, get_source
from msg_src_adapter import get_adapter_by_ctx as get_adapter

__registry__ = cr = CommandRegistry()

_cmd_help = 'admin.help'

_state_machines = {}

_ba = ScoreBizAdapter(config.get('biz_server', [])[0])


@cr.register('test')
@cr.restrict(full_command_only=True, superuser_only=True)
def test(_, ctx_msg):
    core.echo('Your are the superuser!', ctx_msg)


@cr.register('help')
@cr.restrict(full_command_only=True, superuser_only=True)
def help(args_text, ctx_msg, allow_interactive=True):
    _check_admin_group(ctx_msg)

    source = get_source(ctx_msg)
    if allow_interactive and (not args_text or has_session(source, _cmd_help)):
        # Be interactive
        return _help_interactively(args_text, ctx_msg, source)

    if args_text == '1':
        core.echo(
            '(1)设置系统参数：admin.set_param \n<name>,<value>\n'
            '(2)查询系统参数：admin.get_param \n<name>',
            ctx_msg
        )
    elif args_text == '2':
        core.echo(
            '(1)查询白名单：admin.allow_list\n'
            '(2)查询黑名单：admin.block_list\n'
            '(3)设置群白名单：admin.allow_group \n<account-to-allow>\n'
            '(4)设置群黑名单：admin.block_group \n<account-to-block>\n'
            '(5)取消群白名单：admin.unallow_group \n<account-to-allow>\n'
            '(6)取消群黑名单：admin.unblock_group \n<account-to-block>',
            ctx_msg
        )
    elif args_text == '3':
        core.echo(
            '(1)查询发言清洗规则：speak.wash_list\n'
            '(2)设置发言清洗规则：speak.wash \n<rule-for-wash>,<replace-to-wash>\n'
            '(3)取消发言清洗规则：speak.unwash \n<rule-for-wash>,<replace-to-wash>',
            ctx_msg
        )
    elif args_text == '4':
        core.echo(
            '(1)查询群发言总数：speak.total \n<group_id>,<YYYY-MM-DD>\n'
            '(2)查询群发言Top X：speak.top \n<count>,<group_id>,<YYYY-MM-DD>\n'
            '(3)查询群有效发言Top X：speak.vaildtop \n<count>,<group_id>,<YYYY-MM-DD>\n'
            '(4)查询群成员发言数：speak.query \n<nick|qq>,<group_id>,<YYYY-MM-DD>\n'
            '(5)更新群有效发言数据：speak.updatewash <group_id>,<YYYY-MM-DD>',
            ctx_msg
        )
    else:
        core.echo(
            '不支持此指令参数，请重新发起命令',
            ctx_msg
        )


@cr.register('allow_group', 'allow-group')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def allow_group(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('group', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.allow_group <groupid-to-unallow>', ctx_msg)
        return

    if _set_targetlist('allow', 'group', argv[0]):
        core.echo('成功允许群:' + argv[0], ctx_msg)
    else:
        core.echo('未允许群:' + argv[0], ctx_msg)


@cr.register('allow_discuss', 'allow-discuss')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def allow_discuss(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('discuss', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.allow_discuss <discussid-to-unallow>', ctx_msg)
        return

    if _set_targetlist('allow', 'discuss', argv[0]):
        core.echo('成功允许组:' + argv[0], ctx_msg)
    else:
        core.echo('未允许组:' + argv[0], ctx_msg)


@cr.register('allow_private', 'allow-private')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def allow_private(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('private', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.allow_private <account-to-unallow>', ctx_msg)
        return

    if _set_targetlist('allow', 'private', argv[0]):
        core.echo('成功允许单聊:' + argv[0], ctx_msg)
    else:
        core.echo('未允许单聊:' + argv[0], ctx_msg)


@cr.register('allow_list', 'allow-list')
@cr.restrict(full_command_only=True, superuser_only=True)
def allow_list(_, ctx_msg, internal=False):
    if not internal:
        _check_admin_group(ctx_msg)

    targets = _get_targetlist('allow')

    if internal:
        return targets
    if targets:
        core.echo('已允许：\n' + ', '.join(targets), ctx_msg)
    else:
        core.echo('尚未有允许设置', ctx_msg)


@cr.register('unallow_group', 'unallow-group')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def unallow_group(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('group', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.unallow_group <groupid-to-unallow>', ctx_msg)
        return

    if _del_targetlist('allow', 'group', argv[0]):
        core.echo('成功取消允许群:' + argv[0], ctx_msg)
    else:
        core.echo('未取消允许群:' + argv[0], ctx_msg)


@cr.register('unallow_discuss', 'unallow-discuss')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def unallow_discuss(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('discuss', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.unallow_discuss <discussid-to-unallow>', ctx_msg)
        return

    if _del_targetlist('allow', 'discuss', argv[0]):
        core.echo('成功取消允许组:' + argv[0], ctx_msg)
    else:
        core.echo('未取消允许组:' + argv[0], ctx_msg)


@cr.register('unallow_private', 'unallow-private')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def unallow_private(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('private', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.unallow_private <account-to-unallow>', ctx_msg)
        return

    if _del_targetlist('allow', 'private', argv[0]):
        core.echo('成功取消允许群:' + argv[0], ctx_msg)
    else:
        core.echo('未取消允许群:' + argv[0], ctx_msg)


@cr.register('block_group', 'block-group')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def block_group(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('group', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.block_group <groupid-to-unblock>', ctx_msg)
        return

    if _set_targetlist('block', 'group', argv[0]):
        core.echo('成功屏蔽群:' + argv[0], ctx_msg)
    else:
        core.echo('未屏蔽群:' + argv[0], ctx_msg)


@cr.register('block_discuss', 'block-discuss')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def block_discuss(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('discuss', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.block_discuss <discussid-to-unblock>', ctx_msg)
        return

    if _set_targetlist('block', 'discuss', argv[0]):
        core.echo('成功屏蔽组:' + argv[0], ctx_msg)
    else:
        core.echo('未屏蔽组:' + argv[0], ctx_msg)


@cr.register('block_private', 'block-private')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def block_private(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('private', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.block_private <account-to-unblock>', ctx_msg)
        return

    if _set_targetlist('block', 'private', argv[0]):
        core.echo('成功屏蔽单聊:' + argv[0], ctx_msg)
    else:
        core.echo('未屏蔽单聊:' + argv[0], ctx_msg)


@cr.register('block_list', 'block-list')
@cr.restrict(full_command_only=True, superuser_only=True)
def block_list(_, ctx_msg, internal=False):
    if not internal:
        _check_admin_group(ctx_msg)

    targets = _get_targetlist('block')

    if internal:
        return targets
    if targets:
        core.echo('已屏蔽：\n' + ', '.join(targets), ctx_msg)
    else:
        core.echo('尚未有屏蔽设置', ctx_msg)


@cr.register('unblock_group', 'unblock-group')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def unblock_group(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('group', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.unblock_group <groupid-to-unblock>', ctx_msg)
        return

    if _del_targetlist('block', 'group', argv[0]):
        core.echo('成功取消屏蔽群:' + argv[0], ctx_msg)
    else:
        core.echo('未取消屏蔽群:' + argv[0], ctx_msg)


@cr.register('unblock_discuss', 'unblock-discuss')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def unblock_discuss(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('discuss', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.unblock_discuss <discussid-to-unblock>', ctx_msg)
        return

    if _del_targetlist('block', 'discuss', argv[0]):
        core.echo('成功取消屏蔽组:' + argv[0], ctx_msg)
    else:
        core.echo('未取消屏蔽组:' + argv[0], ctx_msg)


@cr.register('unblock_private', 'unblock-private')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=1)
def unblock_private(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    target = _get_target_by_type('private', argv)

    if not target:
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.unblock_private <account-to-unblock>', ctx_msg)
        return

    if _del_targetlist('block', 'private', argv[0]):
        core.echo('成功取消屏蔽群:' + argv[0], ctx_msg)
    else:
        core.echo('未取消屏蔽群:' + argv[0], ctx_msg)


@cr.register('set_param', 'set-param')
@cr.restrict(full_command_only=True, superuser_only=True, allow_private=True)
@split_arguments(maxsplit=2)
def set_param(_, ctx_msg, argv=None):
    if ctx_msg['msg_type'] == 'group':
        _check_admin_group(ctx_msg)
    elif not get_adapter(ctx_msg).is_sender_superuser(ctx_msg):
        raise CommandPermissionError

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nadmin.set_param <name>,<value>', ctx_msg)

    if len(argv) != 2:
        _send_error_msg()
        return

    if _ba.put('/botparam', name=argv[0], value=argv[1]) is not None:
        core.echo('成功设置系统参数[' + argv[0] + ']:' + argv[1], ctx_msg)
    else:
        core.echo('未设置系统参数[' + argv[0] + ']:' + argv[1], ctx_msg)


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
    param = _read_param(argv[0])
    if param:
        core.echo('系统参数[' + argv[0] + ']:' + str(param.get('value')), ctx_msg)
    else:
        core.echo('尚未有设置该系统参数', ctx_msg)


def _help_interactively(args_text, ctx_msg, source):
    def wait_for_type(s, a, c):
        core.echo('你好，超级管理员！请输入你要查找的命令类型：\n'
                  '[1]:基础系统命令\n'
                  '[2]:拦截放行命令\n'
                  '[3]:发言设置命令\n'
                  '[4]:发言管理命令',
                  c)
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


def _get_target_by_type(type, argv=None):
    if len(argv) != 1:
        return False

    target = get_target({
        'via': 'default',
        'msg_type': type,
        {'group': 'group_id', 'discuss': 'discuss_id', 'private': 'sender_id'}.get(type): argv[0]
    })
    return target


def _set_targetlist(type, target_type, account):
    try:
        _ba.put('/' + type + '_' + target_type, account=account)
        result = True
    except:
        result = False

    return result


def _get_targetlist(type):
    rules = _ba.get('/' + type + '_list')['params']
    targets = list(set([x.get('target') for x in rules]))  # Get targets and remove duplications
    return targets


def _del_targetlist(type, target_type, account):
    try:
        _ba.delete('/' + type + '_' + target_type, account=account)
        result = True
    except:
        result = False

    return result


def _read_param(name):
    return _ba.get('/botparam', name=name)


def _check_admin_group(ctx_msg):
    if ctx_msg.get('msg_type', '') == 'group':
        if _read_param('admin_group').get('value') != ctx_msg.get('group_id', ''):
            # core.echo('此命令只能在管理组中使用', ctx_msg)
            raise CommandScopeError('非管理组')
        else:
            return True
