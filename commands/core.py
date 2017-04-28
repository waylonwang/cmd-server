from command import CommandRegistry
from msg_src_adapter import get_adapter_by_ctx
from commands.admin import _exchange_ctx_msg

__registry__ = cr = CommandRegistry()


@cr.register('echo', '重复', '跟我念')
def echo(args_text, ctx_msg, internal=False):
    if internal:
        return None
    else:
        ctx_msg = _exchange_ctx_msg(ctx_msg, 'out')
        return get_adapter_by_ctx(ctx_msg).send_message(
            target=ctx_msg,
            content=args_text
        )


# @cr.register('help', '帮助', '用法', '使用帮助', '使用指南', '使用说明', '使用方法', '怎么用')
# def help(_, ctx_msg):
#     echo(
#         '你好！我是 CCZU 小开机器人，由常州大学开发者协会开发。\n'
#         '我可以为你做一些简单的事情，如发送知乎日报内容、翻译一段文字等。\n'
#         '下面是我现在能做的一些事情：\n\n'
#         '(1)／查天气 常州\n'
#         '(2)／翻译 こんにちは\n'
#         '(3)／翻译到 英语 你好\n'
#         '(4)／历史上的今天\n'
#         '(5)／知乎日报\n'
#         '(6)／记笔记 笔记内容\n'
#         '(7)／查看所有笔记\n'
#         '(8)／查百科 常州大学\n'
#         '(9)／说个笑话\n'
#         '(10)／聊天 你好啊\n\n'
#         '把以上内容之一（包括斜杠，不包括序号，某些部分替换成你需要的内容）发给我，我就会按你的要求去做啦。\n'
#         '上面只给出了 10 条功能，还有更多功能和使用方法，请查看 http://t.cn/RIr177e\n\n'
#         '祝你使用愉快～',
#         ctx_msg
#     )


@cr.register('adminhelp', 'admin-help', 'admin_help')
@cr.restrict(superuser_only=True,allow_private=True, allow_discuss=False, allow_group=False)
def adminhelp(_, ctx_msg):
    echo(
        '你好，超级管理员！\n'
        '(1)设置白名单：admin.allow \ngroup|discuss|private,<account-to-block>\n'
        '(2)设置黑名单：admin.block \ngroup|discuss|private,<account-to-block>\n'
        '(3)取消白名单：admin.unallow \ngroup|discuss|private,<account-to-block>\n'
        '(4)取消黑名单：admin.unblock \ngroup|discuss|private,<account-to-block>\n'
        '(5)查询白名单：admin.allow_list\n'
        '(6)查询黑名单：admin.block_list',
        ctx_msg
    )
    echo(
        '(7)设置交换名单：admin.exchange \nin|out,<account-orig>,<account-dest>\n'
        '(8)取消交换名单：admin.unexchange \nin|out,<account-orig>,<account-dest>\n'
        '(9)查询交换名单：admin.exchange_list\n'
        '(10)设置最低发言字数：admin.set_param \n<name>,<value>\n'
        '(11)查询最低发言字数：admin.get_param \n<value>',
        '(12)查询群成员发言数：speak.query_today \n<nick|qq>,<group_id>',
        ctx_msg
    )
