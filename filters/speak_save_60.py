"""
This filter just log message to stdout.
"""

from filter import as_filter
from commands import speak


@as_filter(priority=60)
def _save_message(ctx_msg):
    speak.speak_record('',ctx_msg)