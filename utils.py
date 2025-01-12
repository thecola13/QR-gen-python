import sys

class CapacityError(ValueError):
    """ Raised when the capacity of the QR code is exceeded """
    pass

class PathError(ValueError):
    """ Raised when the path to the file is invalid """
    pass

class bc_colors:
    """ Look-up table for bash colors """
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def console_log(message, type = 'info', verbosity = 3, threshold = 3):
    """ Helper function for logging messages to the console 
    
    Args:
        message (str): The message to be logged.
        type (str, optional): The type of message. Default is 'info'.
        verbosity (int, optional): The verbosity level of the script. Default is 3.
        threshold (int, optional): The threshold for logging messages. Default is 3.
    """

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
    """" Helper function to convert a bytearray to a string of hexadecimal values 
    Args:
        bytearray (bytearray): The bytearray to be converted.

    Returns:
        str: A string of hexadecimal values separated by spaces.
    """

    s = ''
    for b in bytearray:
        s += f"{b:02X} "
    return s

def handle_error(e, verb):
    """ Helper function to handle exceptions and log them to the console 
    Args:
        e (Exception): The exception object.
        verb (int): The verbosity level of the script.
    """
    console_log(f"An error occurred: {e}", 'error', verb, 0)
    sys.exit(1)