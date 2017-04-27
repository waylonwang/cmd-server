"""
This filter intercepts messages from blocked targets (blocked using sudo.block command).
"""

from commands import scope
from filter import as_filter
from little_shit import get_target


@as_filter(priority=500)
def _filter(ctx_msg):
    target = get_target(ctx_msg)
    if not target:
        return False

    if target[0:2] + '*' in scope.allow_list('', ctx_msg, internal=True):
        return True
    elif target in scope.allow_list('', ctx_msg, internal=True):
        return True
    else:
        return False
