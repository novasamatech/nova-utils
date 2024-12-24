debug_log_enabled = False

def debug_log(message: str):
    if debug_log_enabled:
        print(message)

def set_debug_log_enabled(enabled: bool):
    global debug_log_enabled
    debug_log_enabled = enabled

def enable_debug_log():
   set_debug_log_enabled(True)

def disable_debug_log():
    set_debug_log_enabled(False)