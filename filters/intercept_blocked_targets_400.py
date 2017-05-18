"""
This filter intercepts messages from blocked targets (blocked using setting.block_group command).
"""

from commands import setting
from filter import as_filter
from little_shit import get_target
from msg_src_adapter import get_adapter_by_ctx


@as_filter(priority=400)
def _filter(ctx_msg):
    if get_adapter_by_ctx(ctx_msg).is_sender_superuser(ctx_msg):
        return True

    target = get_target(ctx_msg)
    if not target:
        return True

    if target[0:2] + '*' in setting.block_list('', ctx_msg, internal=True):
        return False
    elif target in setting.block_list('', ctx_msg, internal=True):
        return False
    else:
        return True
