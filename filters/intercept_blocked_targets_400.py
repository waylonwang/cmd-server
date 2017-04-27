"""
This filter intercepts messages from blocked targets (blocked using sudo.block command).
"""

from commands import scope
from filter import as_filter
from little_shit import get_target


@as_filter(priority=400)
def _filter(ctx_msg):
    target = get_target(ctx_msg)
    if not target:
        return True

    if target[0:2] + '*' in scope.block_list('', ctx_msg, internal=True):
        return False
    elif target in scope.block_list('', ctx_msg, internal=True):
        return False
    else:
        return True
