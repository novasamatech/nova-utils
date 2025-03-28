from scripts.xcm_transfers.utils.colored_text import colored, bcolors

debug_log_enabled = False

def debug_log(message: str):
    if debug_log_enabled:
        print(message)

def warn_log(message: str):
    print(colored(message, bcolors.WARNING))

def set_debug_log_enabled(enabled: bool):
    global debug_log_enabled
    debug_log_enabled = enabled

def enable_debug_log():
   set_debug_log_enabled(True)

def disable_debug_log():
    set_debug_log_enabled(False)
