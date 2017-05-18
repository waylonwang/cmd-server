"""
This filter intercepts messages from blocked targets (blocked using sudo.block command).
"""

from filter import as_filter


@as_filter(priority=600)
def _filter(ctx_msg):
    # ctx_msg=exchange_ctx_msg(ctx_msg,'in') exchange作用已经不大，去除exchange
    return True
