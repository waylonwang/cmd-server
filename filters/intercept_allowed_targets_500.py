"""
This filter intercepts messages from allowed targets (allowed using setting.allow_group command).
"""
from commands import setting
from filter import as_filter
from little_shit import get_target
from msg_src_adapter import get_adapter_by_ctx


@as_filter(priority=500)
def _filter(ctx_msg):
    if get_adapter_by_ctx(ctx_msg).is_sender_superuser(ctx_msg):
        return True

    target = get_target(ctx_msg)
    if not target:
        return False

    if target[0:2] + '*' in setting.allow_list('', ctx_msg, internal=True):
        return True
    elif target in setting.allow_list('', ctx_msg, internal=True):
        return True
    else:
        return False
