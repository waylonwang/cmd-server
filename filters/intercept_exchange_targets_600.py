"""
This filter intercepts messages from blocked targets (blocked using sudo.block command).
"""

from commands.scope import exchange_ctx_msg
from filter import as_filter
from little_shit import get_target


@as_filter(priority=600)
def _filter(ctx_msg):
    # ctx_msg=exchange_ctx_msg(ctx_msg,'in')
    return True

