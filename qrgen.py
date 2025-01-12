from qrcode import genqr
from visualization import render_qr
from utils import handle_error, console_log
from argparse import ArgumentParser, RawDescriptionHelpFormatter


def main():
    """
    Main function to parse command-line arguments and generate a QR Code.

    This function sets up an argument parser to handle various command-line options for generating a QR Code.
    It validates the input data, generates the QR Code, and saves it to the specified output file.

    Command-line arguments:
        --data, -d (str): Link or data to be encoded in QR Code. Characters not in UTF-8 might cause failures. (required)
        --output, -o (str): Output file path (default: ./qrcode.png).
        --resolution, -r (int): Resolution of the QR Code in pixels (default: 300 x 300).
        --minversion, -mv (int): Force the minimum version of the QR Code (default: 1).
        --maxversion, -Mv (int): Force the maximum version of the QR Code (default: 40). Be aware that a low enough minimum version could result in failures.
        --ecl, -e (str): Minimum error correction level: L (7%), M (15%), Q (25%), H (30%) (default: M).
        --verbosity, -v (int): Verbosity level of the script (default: 0).
    """

    parser = ArgumentParser(prog = 'qrgen',
                            formatter_class = RawDescriptionHelpFormatter,
                            usage = '''qrgen [-h] --l <link> [--output <output>] [--resolution <resolution>] 
             [--minversion <minversion>] [--maxversion <maxversion>] [--ecl <ecl>] [--verbosity <verbosity>]''',

                            description = '''A simple CLI QR Code generator in Python, loosely based on Project Nayuki\'s 
tutorial on QR Code generation. The script generates a QR Code from a given
link or payload, allowing the user to specify the output file path, resolution,
minimum and maximum versions, and error correction level.''', 

                            epilog = '''Developed by Luca Colaci as a personal project for the 20875 - Software Engineering course at Bocconi University.''')

    parser.add_argument('--data', '-d', type = str, help = 'Link or data to be encoded in QR Code. Characters not in UTF-8 might cause failures.', required = True)
    parser.add_argument('--output', '-o', default = 'qrcode.png', type = str, help = 'Output file path (default: ./qrcode.png)', required = False)
    parser.add_argument('--resolution', '-r', default = 300, type = int, help = 'Resolution of the QR Code in pixels (default: 300 x 300).', required = False)
    parser.add_argument('--minversion', '-mv', default = 1, type = int, help = 'Force the minimum version of the QR Code (default: 1).', required = False)
    parser.add_argument('--maxversion', '-Mv', default = 40, type = int, help = 'Force the maximum version of the QR Code (default: 40). Be aware that a low enough maximum version could result in failures.', required = False)
    parser.add_argument('--ecl', '-e', default = 'M', type = str, help = 'Minimum error correction level: L (7%%), M (15%%), Q (25%%), H (30%%) (default: M).', required = False)
    parser.add_argument('--verbosity', '-v', default = 0, type = int, help = 'Verbosity level of the script (default: 0).', required = False)

    args = parser.parse_args()

    if check_encoding(args.data):
        console_log("Data is in UTF-8 format.", 'success', args.verbosity, 0)
        gen_qr(args.data, args.minversion, args.maxversion, args.ecl, args.verbosity, args.resolution, args.output)
    else:
        console_log("Data is not in UTF-8 format. Please provide a valid payload.", 'error', args.verbosity, 2)

def check_encoding(payload):
    """
    Check if the payload is in UTF-8 format.

    Args:
        payload (str): The payload to be checked.

    Returns:
        bool: True if the payload is in UTF-8 format, False otherwise.
    """
    try:
        checked_payload = payload.encode('utf-8')
        return True
    except:
        return False
    
def gen_qr(data, minversion, maxversion, ecl, verbosity, resolution, output):
    """
    Generate a QR Code from the given data.

    Args:
        data (str): Link or data to be encoded in QR Code.
        minversion (int): Force the minimum version of the QR Code.
        maxversion (int): Force the maximum version of the QR Code.
        ecl (str): Minimum error correction level: L (7%), M (15%), Q (25%), H (30%).
        verbosity (int): Verbosity level of the script.
    """
    try:
        qr = genqr(data, minversion, maxversion, ecl, verbosity)
        img = render_qr(qr, resolution, 2, verbosity)
        img.save(output)
        console_log(f"QR Code successfully saved to {output}!", 'success', verbosity, 0)
    except Exception as e:
        handle_error(e, verbosity)

if __name__ == '__main__':
    main()


