"""
This filter save message to database.
"""

from commands import speak
from filter import as_filter


@as_filter(priority=60)
def _save_message(ctx_msg):
    speak.speak_record('', ctx_msg)
    pass
