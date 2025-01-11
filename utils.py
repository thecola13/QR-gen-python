class CapacityError(ValueError):
    pass

class bc_colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def console_log(message, type = 'info', verbosity = 3, threshold = 3):
    if verbosity >= threshold:
        if type == 'info':
            print(f"{bc_colors.BLUE}[INFO] {message} {bc_colors.ENDC}")
        elif type == 'warning':
            print(f"{bc_colors.WARNING}[WARNING] {message}{bc_colors.ENDC}")
        elif type == 'error':
            print(f"{bc_colors.FAIL}[ERROR] {message} {bc_colors.ENDC}")
        elif type == 'success':
            print(f"{bc_colors.GREEN}[SUCCESS] {message} {bc_colors.ENDC}")
        else:
            print(f"[{type}] {message}")
    else:
        pass

def stringify_bytearray(bytearray):
    s = ''
    for b in bytearray:
        s += f"{b:02X} "
    return s

def handle_error(e, verb):
    console_log(f"An error occurred: {e}", 'error', verb, 0)