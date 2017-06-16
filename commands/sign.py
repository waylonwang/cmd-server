
from config import config
from biz_adapters.score_biz_server import ScoreBizAdapter
from command import CommandRegistry, split_arguments
from little_shit import check_target, get_target_account

__registry__ = cr = CommandRegistry()
__target_prefix = {'group': 'group_id', 'discuss': 'discuss_id', 'private': 'sender_id'}

_ba = ScoreBizAdapter(config.get('biz_server', [])[0])

@cr.register('签到')
@split_arguments(maxsplit=1)
@check_target
def sign(_, ctx_msg, argv=None):
    target_type = ctx_msg.get('msg_type')
    target_account = get_target_account(ctx_msg)
    member_id = ctx_msg.get('sender_id')
    member_name = ctx_msg.get('sender_name')
    message = ctx_msg.get('content')

    _ba.post('/sign',
             target_type=target_type,
             target_account=target_account,
             member_id=member_id,
             member_name=member_name,
             message=message)
