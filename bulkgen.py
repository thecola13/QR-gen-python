import os
from qrgen import gen_qr, check_encoding
from utils import console_log, handle_error, CustomArgParser
from argparse import RawDescriptionHelpFormatter

def main(): 
    """
    Main function to parse command-line arguments and bulk-generate QR Codes.

    This function sets up an argument parser to handle various command-line options for generating multiple QR Codes.
    It validates the input data, generates the QR Codes, and saves them to the specified output directory.
    """

    parser = CustomArgParser(prog = 'bulkgen',
                            formatter_class = RawDescriptionHelpFormatter,
                            usage = '''bulkgen [-h] --file <file> [--output <output>] [--resolution <resolution>] 
             [--minversion <minversion>] [--maxversion <maxversion>] [--ecl <ecl>] [--verbosity <verbosity>]''',

                            description = '''A simple CLI QR Code bulk generator in Python, loosely based on Project Nayuki\'s 
tutorial on QR Code generation. The script generates QR Codes from a given 
file containing links or payloads, allowing the user to specify the output 
directory, resolution, min and maxm versions, error correction level and extension.''',

                            epilog = '''Developed by Luca Colaci as a personal project for the 20875 - Software Engineering course at Bocconi University.''')
    
    parser.add_argument('--file', '-f', type = str, help = 'File containing links or data to be encoded in QR Codes. Characters not in UTF-8 might cause failures.', required = True)
    parser.add_argument('--output', '-o', default = 'qrcodes', type = str, help = 'Output directory path (default: ./qrcodes)', required = False)
    parser.add_argument('--resolution', '-r', default = 300, type = int, help = 'Resolution of the QR Codes in pixels (default: 300 x 300).', required = False)
    parser.add_argument('--minversion', '-mv', default = 1, type = int, help = 'Force the minimum version of the QR Codes (default: 1).', required = False)
    parser.add_argument('--maxversion', '-Mv', default = 40, type = int, help = 'Force the maximum version of the QR Codes (default: 40). Be aware that a low enough maximum version could result in failures.', required = False)
    parser.add_argument('--ecl', '-e', default = 'M', type = str, help = 'Minimum error correction level: L (7%%), M (15%%), Q (25%%), H (30%%) (default: M).', required = False)
    parser.add_argument('--extension', '-ext', default = 'png', type = str, help = 'Output format of the image (default: .png).', required = False)
    parser.add_argument('--verbosity', '-v', default = 0, type = int, help = 'Verbosity level of the script (default: 0).', required = False)

    try:
        args = parser.parse_args()
    except Exception as e:
        handle_error(e, 0)

    if not os.path.exists(args.output):
        try:
            os.makedirs(args.output)
        except OSError as e:
            handle_error(e, 'directory', args.output, args.verbosity, 2)
        else:
            console_log(f"Output directory {args.output} created successfully.", 'success', args.verbosity, 2)

    with open(args.file, 'r') as f:
        data = f.readlines()
        for i, line in enumerate(data):
            if check_encoding(line):
                console_log(f"Working on QR Code {i}", 'info', args.verbosity, 1)
                output_path = f"{args.output}/qrcode_{i}.{args.extension}"
                gen_qr(line, args.minversion, args.maxversion, args.ecl, args.verbosity, args.resolution, output_path)

            else:
                console_log(f"Data in line {i} is not in UTF-8 format. Please provide a valid payload.", 'error', args.verbosity, 0)

        console_log(f"QR Codes generated successfully. Check the output directory at {args.output}.", 'success', args.verbosity, 0)
    



if __name__ == '__main__':
    main()