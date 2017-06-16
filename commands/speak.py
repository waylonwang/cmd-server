from datetime import datetime

from pytz import timezone
from sqlalchemy.ext.declarative import declarative_base

from biz_adapters.score_biz_server import ScoreBizAdapter
from command import CommandRegistry, split_arguments
from commands import core
from commands.setting import _check_admin_group
from config import config
from little_shit import check_target, get_target_account

Base = declarative_base()

__registry__ = cr = CommandRegistry()

_ba = ScoreBizAdapter(config.get('biz_server', [])[0])


@check_target
def speak_record(_, ctx_msg):
    target_type = ctx_msg.get('msg_type')
    target_account = get_target_account(ctx_msg)
    sender_id = ctx_msg.get('sender_id')
    sender_name = ctx_msg.get('sender_name')
    message = ctx_msg.get('content')

    _ba.post('/speakrecord',
             target_type=target_type,
             target_account=target_account,
             sender_id=sender_id,
             sender_name=sender_name,
             message=message)


@cr.register('查询-发言')
@check_target
def speak_query(args_text, ctx_msg):
    if len(args_text) == 0:
        user = None
        utext = '你'
    else:
        user = args_text
        utext = user.replace('@', '', 1)

    result = _queryspeak(ctx_msg, user=user)
    if result is None:
        core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] ' + utext + '今天共发言:' + str(result['count_full'])
                  + ',有效发言:' + str(result['count_valid']), ctx_msg)
    else:
        core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] ' + utext + '今天共发言:' + str(result['count_full'])
                  + ',有效发言:' + str(result['count_valid']), ctx_msg)
    return


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

    result = _ba.put('/speakwash', rule=argv[0], replace=argv[1])

    if result is None:
        core.echo('未添加清洗规则[' + _escape(argv[0]) + ' -> ' + argv[1], ctx_msg)
    else:
        core.echo('成功添加清洗规则 ' + _escape(argv[0]) + ' -> ' + argv[1], ctx_msg)
    return


@cr.register('wash_list', 'wash-list')
@cr.restrict(full_command_only=True, superuser_only=True)
def wash_list(_, ctx_msg, internal=False):
    if not internal:
        _check_admin_group(ctx_msg)

    rules = _ba.get('/speakwashs')
    result = list(set([_escape(x['rule']) + ' , ' + x['replace'] for x in rules.get('rules')]))
    if internal:
        return result
    if result is None:
        core.echo('尚未有清洗规则设置', ctx_msg)
        return
    else:
        core.echo('已有清洗规则：\n' + '\n'.join(result), ctx_msg)
    return


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

    result = _ba.delete('/speakwash', rule=argv[0])
    if result is None:
        core.echo('未取消清洗规则 ' + _escape(argv[0]) + ' -> ' + argv[1], ctx_msg)
        return
    else:
        core.echo('成功取消清洗规则 ' + _escape(argv[0]) + ' -> ' + argv[1], ctx_msg)
    return


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

    result = _ba.patch('/speakwashupdate',
                       target_type='group',
                       target_account=argv[0],
                       date_from=argv[1],
                       date_to=argv[1])

    core.echo('即将开始更新' + argv[1] + '[' + argv[0] + ']' + '的发言数据，耗时可能较长，请耐心等候！', ctx_msg)
    if result is None:
        core.echo('未更新' + argv[1] + '[' + argv[0] + ']' + '有效发言数据', ctx_msg)
        return
    else:
        core.echo('成功更新' + argv[1] + '[' + argv[0] + ']' + '有效发言数据', ctx_msg)
    return


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

    result = _queryspeak(ctx_msg, user=argv[0], target_type='group', target_account=argv[1], date=argv[2])
    if result is None:
        core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']发言查询失败', ctx_msg)
    else:
        core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] ' + argv[0].replace('@', '', 1) + ' ' + argv[2] +
                  '在[' + str(argv[1]) + ']共发言:' + str(result['count_full']) +
                  ',有效发言:' + str(result['count_valid']), ctx_msg)
    return


def _queryspeak(ctx_msg, user=None, target_type=None, target_account=None, date=None):
    # ctx_msg = _exchange_ctx_msg(ctx_msg, 'in')

    if date == None:
        date = datetime.now(tz=timezone('Asia/Shanghai')).strftime('%Y-%m-%d')

    if target_type is None:
        target_type = ctx_msg.get('msg_type')

    if target_account is None:
        target_account = get_target_account(ctx_msg)

    if user == None:
        user = ctx_msg.get('sender_id', '')
    else:
        user = user.replace('@', '', 1)

    result = _ba.get('/speakcount',
                     target_type=target_type,
                     target_account=target_account,
                     sender=user,
                     date_from=date,
                     date_to=date)

    if result is None:
        result = {'count_full': 0, 'count_valid': 0}

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

    result = _ba.get('/speaktotal',
                     target_type='group',
                     target_account=argv[0],
                     date_from=argv[1],
                     date_to=argv[1])

    if result is None:
        core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']发言统计失败', ctx_msg)
    else:
        core.echo(
            '[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[0]) + ']' + argv[1] + '共发言:' + str(
                result['count_full']) + ',有效发言:' + str(
                result['count_valid']), ctx_msg)
    return


@cr.register('top', 'top')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=3)
def top(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.top <count>,<group_id>,<YYYY-MM-DD>', ctx_msg)

    if len(argv) != 3:
        _send_error_msg()
        return

    if not _get_top(ctx_msg, 0, argv):
        core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[1]) + ']发言统计失败', ctx_msg)
    return


@cr.register('vaildtop', 'vaildtop')
@cr.restrict(full_command_only=True, superuser_only=True)
@split_arguments(maxsplit=3)
def vaildtop(_, ctx_msg, argv=None):
    _check_admin_group(ctx_msg)

    def _send_error_msg():
        core.echo('参数不正确。\n\n正确使用方法：\nspeak.vaildtop <count>,<group_id>,<YYYY-MM-DD>', ctx_msg)

    if len(argv) != 3:
        _send_error_msg()
        return

    if not _get_top(ctx_msg, 1, argv):
        core.echo('[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[1]) + ']发言统计失败', ctx_msg)
    return


def _get_top(ctx_msg, is_valid, argv):
    result = _ba.get('/speaktop',
                     target_type='group',
                     target_account=argv[1],
                     date_from=argv[2],
                     date_for=argv[2],
                     limit=argv[0],
                     is_valid=is_valid)

    if result is None:
        return False

    strTitle = '发言前'
    if is_valid:
        strTitle = '有效' + strTitle

    msg = '[CQ:at,qq=' + ctx_msg.get('sender_id') + '] [' + str(argv[1]) + ']' + argv[2] + strTitle + str(argv[0]) + ':'
    i = 1
    msglist = []
    for x in result:
        msg = msg + '\n' + str(i) + '.' + x['toprank']['sender_name'] + '(' + x['toprank']['sender_id'] + '):' + str(
            x['toprank']['cnt'])
        if i % 5 == 0:
            msglist.append(msg)
            msg = '[CQ:at,qq=' + ctx_msg.get('sender_id') + ']'
        i = i + 1
    if (i - 1) % 5 != 0:
        msglist.append(msg)
    for k, v in enumerate(msglist):
        core.echo(v, ctx_msg)
    return True


def _escape(args_text):
    return args_text.replace('&', '%26amp%3b').replace('[', '%26%2391%3b').replace(']', '%26%2393%3b')


