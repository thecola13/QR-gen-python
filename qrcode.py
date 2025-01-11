from utils import CapacityError, console_log, stringify_bytearray

def get_bit(data, index):
    """
    Extracts a specific bit from an integer.

    Args:
        data (int): The integer from which to extract the bit.
        index (int): The position of the bit to extract (0-based).

    Returns:
        int: The value of the bit at the specified position (0 or 1).
    """
    return (data >> index) & 1

class BitStream:
    ''' Helper class to handle bit manipulation '''

    def __init__(self):
        """
        Initializes a new instance of the class.
        Attributes:
            data (list): A list to store data for the QR code.
        """
        self.data = []
    
    def append_bits(self, val, n): 
        """
        Appends the bits of a given value to the data list.
        Args:
            val (int): The value whose bits are to be appended.
            n (int): The number of bits to append from the value.
        Raises:
            ValueError: If n is negative or if the value cannot be represented in n bits.
        """
        
        if n < 0 or (val >> n) != 0: # Checks that the value can be represented in n bits
            raise ValueError("Value out of range")
        else:
            self.data.extend(get_bit(val, i) for i in range(n - 1, -1, -1)) # Extends the storage accordingly

    def __str__(self):
        """
        Returns a string representation of the QR code data.
        
        The string is created by concatenating the string representation of each bit in the data.

        Returns:
            str: A string representation of the QR code data.
        """
        return ''.join(str(bit) for bit in self.data)
    
    def __len__(self):
        """
        Returns the length of the data stored in the QR code object.
        
        Returns:
            int: The length of the data.
        """
        return len(self.data)
    
    def __copy__(self):
        """
        Create a shallow copy of the current BitStream instance.

        Returns:
            BitStream: A new instance of BitStream with a copied data attribute.
        """
        new = BitStream()
        new.data = self.data.copy()
        return new
    
    def copy(self):
        """
        Wrapper function for the __copy__ private method.
        
        Returns:
            object: A new BitStream instance that is a copy of the current instance.
        """
        return self.__copy__()
    
    def __getitem__(self, key):
        """
        Retrieves an item from the data using the given key.
        
        Args:
            key (int or Slice): The key used to access the data.
            
        Returns:
            object: The value associated with the specified key.
        """
        if not isinstance(key, slice) or not isinstance(key, int):
            raise KeyError("Key must be a integer or slice")
        
        return self.data[key]
    
    def convert_to_bytes(self):
        """
        Converts the bit stream to a byte array.

        This method ensures that the length of the bit stream is a multiple of 8.
        If not, it raises a ValueError. It then converts each 8-bit segment of the
        bit stream into a byte and returns the result as a bytearray.

        Returns:
            bytearray: The bytearray representation of the bit stream.
        """
        if len(self) % 8 != 0: # Asserting that the length is a multiple of 8
            raise ValueError("BitStream length not a multiple of 8")

        byte_list = []
        for i in range(0, len(self), 8):
            byte = ''.join(str(bit) for bit in self.data[i:i+8])
            byte_list.append(int(byte, 2))
        return bytearray(byte_list)

class Mode:
    ''' Helper class to handle mode bits and character count indicators '''

    def __init__(self, modebits, charcount):
        '''
        Initializes a new instance of the class.
        Args:
            modebits (int): The mode bits for the mode.
            charcount (tuple): The number of character count bits for each version.
        '''
        self.modebits = modebits
        self.charcount = charcount
    
    def get_num_char_count_bits(self, version):
        """
        Returns the number of character count bits for a given QR code version.
        
        Args:
            version (int): The version of the QR code (must be between 1 and 40 inclusive).
        
        Returns:
            int: The number of character count bits for the specified version.
        """
        if 1 <= version <= 40:
            return self.charcount[(version + 7) // 17]
        else:
            raise ValueError("Invalid version")

byte_mode = Mode(0x4, (8, 16, 16)) # Initializing byte mode lookup variable

# Lookup table for error correction code words
ecl_lookup = {
    'L': (0, 1), # (L)ow:      ordinal = 1, format bits = 1
    'M': (1, 0), # (M)edium:   ordinal = 0, format bits = 0
    'Q': (2, 3), # (Q)uartile: ordinal = 2, format bits = 3
    'H': (3, 2)  # (H)igh:     ordinal = 3, format bits = 2
}


class RSEncoder:
    ''' Helper class to handle Reed-Solomon encoding.'''

    def __init__(self, degree):
        """
        Initializes the QR code generator with the specified error correction degree.
        Args:
            degree (int): The error correction degree for the QR code.
        """
        
        self.degree = degree
        self.div = self.create_rs_divisor(degree) # Stores the divisor for the Reed-Solomon encoding

    def create_rs_divisor(self, degree):
        """
        Creates a Reed-Solomon divisor polynomial for error correction.
        Args:
            degree (int): The degree of the polynomial (must be between 1 and 255 inclusive).
        Returns:
            bytearray: The Reed-Solomon divisor polynomial as a bytearray.
        """
        if degree < 1 or degree > 255:
            raise ValueError("Invalid degree")
        
        res = bytearray([0] * (degree - 1) + [1]) # Initializes the divisor as a monomial x^0

        root = 1 # Initializes the root of the polynomial

        for _ in range(degree):
            for j in range(degree):
                res[j] = self.multiply(res[j], root)  # Multiply the current coefficient by the root
                if j+1 < degree:
                    res[j] ^= res[j+1]  # XOR with the next coefficient if within bounds
            
            root = self.multiply(root, 0x02)  # Update the root for the next iteration
        
        return res
    
    def remainder(self, data):
        """
        Computes the remainder of the division of the given data by the divisor.

        Args:
            data (bytearray): The data to be divided.

        Returns:
            bytearray: The remainder of the division.
        """

        res = bytearray([0] * len(self.div)) # Initializes the result as a zero array

        for b in data:
            f = b ^ res.pop(0) # XOR the first element of the result with the current byte
            res.append(0) # Append a zero to the result

            for i, c in enumerate(self.div):
                res[i] ^= self.multiply(c, f)  # XOR the current coefficient with the product of the divisor coefficient and the factor

        return res

    def multiply(self, x, y):
        """
        Multiplies two 8-bit integers in the Galois Field GF(2^8) with the irreducible polynomial x^8 + x^4 + x^3 + x + 1.
        Args:
            x (int): The first 8-bit integer (0 <= x < 256).
            y (int): The second 8-bit integer (0 <= y < 256).
        Returns:
            int: The product of x and y in GF(2^8).
        """
        if (x >> 8 != 0) or (y >> 8 != 0):
            raise ValueError("Invalid input")
        
        z = 0

        for i in range(7, -1, -1):
            z = (z << 1) ^ ((z >> 7) * 0x11D)
            z ^= ((y >> i) & 1) * x
        
        return z


class QR:
    ''' Class to handle QR code generation. '''

    def __init__(self, data, minversion = 1, maxversion = 40, ecl = 'M', mask = -1, verbosity = 0):
        """
        Initializes a QR code object with the given data and parameters.
        Args:
            data (str): The data to be encoded in the QR code.
            minversion (int, optional): The minimum version of the QR code (default is 1).
            maxversion (int, optional): The maximum version of the QR code (default is 40).
            ecl (str, optional): The error correction level (default is 'M'). Must be one of 'L', 'M', 'Q', 'H'.
            mask (int, optional): The mask pattern to be applied (default is -1 for automatic selection).
            verbosity (int, optional): The verbosity level for logging (default is 0).
        """
        console_log(f'Generating QR code for data: {data}', 'info', verbosity, 1)
    

        if not (1 <= minversion <= maxversion <= 40):
            raise ValueError("Invalid version number(s)")
        
        if ecl not in ecl_lookup:
            raise ValueError("Invalid error correction level")
        
        if mask not in range(-1, 8):
            raise ValueError("Invalid mask")
        
        # Tries to minimize the QR code version
        self.version = self.optimize_version(data, minversion, maxversion, ecl, verbosity)
        console_log(f'Optimized version: {self.version}', 'info', verbosity, 2)


        self.ecl = self.optimize_ecl(data, self.version, ecl, verbosity) # Tries to maximize the error correction level for the given version

        if self.ecl != ecl: # Checks if the error correction level has been optimized
            console_log(f'Error correction level optimized from {ecl} to {self.ecl}', 'info', verbosity, 2)
        else:
            console_log(f'Error correction level: {self.ecl}', 'info', verbosity, 2)

        self.size = (self.version * 4) + 17

        self.blocks = [[False] * self.size for _ in range(self.size)]
        self.isfunction = [[False] * self.size for _ in range(self.size)]

        console_log(f'Successfull QR initialization!', 'success', verbosity, 3)

        encoded_payload = pad_and_terminate(data, self.version, ecl)

        console_log(f'Padded payload: {stringify_bytearray(encoded_payload)}', 'info', verbosity, 3)

        self.draw_function_patterns(verbosity) # Draws timing, alignment and finder patterns. Also, draws mock format and version bits for mask selection

        console_log(f'Function patterns successfully drawn!', 'success', verbosity, 3)

        self.payload = self.prepare_payload(encoded_payload, verbosity) # Prepares the payload for encoding
        
        console_log(f'Prepared payload: {stringify_bytearray(self.payload)}', 'info', verbosity, 3)
        console_log(f'Payload prepared for visualization!', 'success', verbosity, 2)

        self.set_data_bytes(verbosity) 

        console_log(f'Data bytes successfully set!', 'success', verbosity, 3)

        console_log(f'Starting mask optimization', 'info', verbosity, 3)

        if mask == -1: 
            min_penalty = float('inf')
            for i in range(8):
                self.apply_mask(i)
                self.set_format_bits(i)

                penalty = self.get_penalty(verbosity)
                console_log(f'Mask {i}: {penalty}', 'info', verbosity, 3)
                if penalty < min_penalty:
                    min_penalty = penalty
                    mask = i
                self.apply_mask(i)
            
            console_log(f'Optimized mask: {mask} (penalty: {min_penalty})', 'success', verbosity, 2)
        
        console_log(f'Applying mask {mask}', 'info', verbosity, 3)

        self.apply_mask(mask)

        console_log(f'Setting format bits', 'info', verbosity, 3)

        self.set_format_bits(mask)

        console_log(f'QR code successfully generated!', 'success', verbosity, 1)

    def optimize_version(self, data, minversion, maxversion, ecl, verbosity):
        """
        Determines the optimal QR code version for the given data within the specified range.
        Args:
            data (str): The data to be encoded in the QR code.
            minversion (int): The minimum QR code version to consider (must be between 1 and 40 inclusive).
            maxversion (int): The maximum QR code version to consider (must be between 1 and 40 inclusive).
            ecl (str): The error correction level (L, M, Q, or H).
            verbosity (int): The verbosity level for logging (0 for no logging, higher values for more detailed logs).
        Returns:
            int: The optimal QR code version that can encode the given data within the specified range.
        """

        for version in range(minversion, maxversion + 1): # Uses a bottom-up approach to find the smallest version that can encode the data
            max_capacity = get_capacity(version, ecl) * 8
            used_capacity = 4 + byte_mode.get_num_char_count_bits(version) + len(data) * 8

            console_log(f'Version {version}: {used_capacity}/{max_capacity}', 'info', verbosity, 3)

            if used_capacity and (used_capacity <= max_capacity): # Checks if the data can fit in the QR code
                break
            
            if version >= maxversion: # If the version is above the maximum, raise an error
                raise CapacityError("The payload is too long to be encoded in a QR code. Try increasing the maximum version, reducing the data or changing the error correction level.")
            
        return version

    def optimize_ecl(self, data, version, ecl, verbosity):
        """
        Optimizes the error correction level (ECL) for the given data and QR code version.

        Args:
            data (str): The data to be encoded in the QR code.
            version (int): The version of the QR code (must be between 1 and 40 inclusive).
            ecl (str): The initial error correction level (one of 'L', 'M', 'Q', 'H').

        Returns:
            str: The optimized error correction level for the given data and QR code version.
        """

        for ecl in ['H', 'Q', 'M', 'L']: # Using a top-down approach to find the highest error correction level that can encode the data
            max_capacity = get_capacity(version, ecl) * 8
            used_capacity = 4 + byte_mode.get_num_char_count_bits(version) + len(data) * 8

            console_log(f'ECL {ecl}: {used_capacity}/{max_capacity}', 'info', verbosity, 3)

            if used_capacity and (used_capacity <= max_capacity):
                break

        return ecl
        
    def set_block(self, x, y, value, isfunction = False):
        """
        Sets the value and function status of a block at the specified coordinates.

        Args:
            x (int): The x-coordinate of the block.
            y (int): The y-coordinate of the block.
            value: The value to set for the block.
            isfunction (bool, optional): Indicates if the block is a function block. Defaults to False.
        """

        self.blocks[y][x] = value
        self.isfunction[y][x] = isfunction

    def draw_function_patterns(self, verbosity = 0):
        """
        Draws the function patterns (timing, finder, alignment, format, and version bits) on the QR code matrix.
        Args:
            verbosity (int, optional): The verbosity level for logging (default is 0).
        Notes:
            - Timing patterns are always set.
            - Finder patterns are set at the top-left, top-right, and bottom-left corners.
            - Alignment patterns are set for versions greater than 1, avoiding overlap with finder patterns.
            - Dummy format bits are set and will be replaced after mask selection.
            - Version bits are set for versions 7 and above.
        """

        console_log(f'Starting function pattern drawing', 'info', verbosity, 4)

        self.set_timing_patterns() # Timing patterns

        console_log(f'Timing patterns successfully set', 'info', verbosity, 4)

        self.set_finder_pattern(0, 0) # Top-left finder
        self.set_finder_pattern(self.size - 7, 0) # Top-right finder
        self.set_finder_pattern(0, self.size - 7) # Bottom-left finder

        console_log(f'Finder patterns successfully set', 'info', verbosity, 4)

        count = 0

        if self.version != 1: # No need alignment patterns for version 1
            align_pos = self.get_alignment_positions() # Retrieves the positions of the alignment patterns
            for x in align_pos:
                for y in align_pos:
                    if (x, y) not in [(6, 6), (6, self.size - 7), (self.size - 7, 6)]: # Avoids overlapping with finder patterns
                        self.set_alignment_pattern(x, y)
                        count += 1

        console_log(f'Alignment patterns successfully set (n = {count})', 'info', verbosity, 4)
        
        self.set_format_bits(-1) # Dummy values, will be replaced after mask selection

        console_log(f'Dummy format bits successfully set', 'info', verbosity, 4)

        if self.version >= 7: # Version bits are only needed for version 7 and above
            self.set_version_bits() # Version bits

            console_log(f'Version bits successfully set for version {self.version}', 'info', verbosity, 4)

    def set_timing_patterns(self):
        """
        Sets the timing patterns for the QR code.

        The timing patterns are alternating black and white modules placed in the 6th row and column of the QR code matrix.
        These patterns help the QR code reader determine the size and orientation of the QR code.

        Args:
            None

        Returns:
            None
        """
        for i in range(self.size):
            self.set_block(6, i, (i % 2 == 0), True)
            self.set_block(i, 6, (i % 2 == 0), True)

    def set_finder_pattern(self, x, y):
        """
        Sets the finder pattern at the specified (x, y) coordinates in the QR code matrix.

        These patterns consist of a 7x7 square of alternating black and white modules with a surrounding border of white modules.
        They allow for the QR code reader to locate and orient the QR code.

        Args:
            x (int): The x-coordinate of the top-left corner of the finder pattern.
            y (int): The y-coordinate of the top-left corner of the finder pattern.
        """
        for i in range(-1, 8):
            for j in range(-1, 8):
                is_dark = (
                    0 <= i <= 6 and 0 <= j <= 6 and
                    (i in [0, 6] or j in [0, 6] or (2 <= i <= 4 and 2 <= j <= 4))
                )
                if 0 <= x + i < self.size and 0 <= y + j < self.size:
                    self.set_block(x + i, y + j, is_dark, True)

    def get_alignment_positions(self):
        """
        Calculates the alignment pattern positions for the QR code based on its version.

        The alignment patterns are around the qr code, but positions might overlap with finder patterns.

        Returns:
            list: A list of integers representing the positions of the alignment patterns.
        """
        num_positions = self.version // 7 + 2
        step = ((self.version * 8 + num_positions * 3 + 5) 
                // (num_positions * 4 - 4) * 2)
        result = [(self.size - 7 - i * step) for i in range(num_positions - 1)] + [6]
        return list(reversed(result))
    
    def set_alignment_pattern(self, x, y):
        """
        Sets the alignment pattern for the QR code at the specified coordinates.

        These alignment patterns consist of a 5x5 square of alternating black and white modules with a surrounding border of white modules.
        They help the QR code reader correct for distortion in the QR code.

        Args:
            x (int): The x-coordinate of the center of the alignment pattern.
            y (int): The y-coordinate of the center of the alignment pattern.
        """
        for i in range(-2, 3):
            for j in range(-2, 3):
                is_dark = max(abs(i), abs(j)) != 1
                self.set_block(x + i, y + j, is_dark, True)

    def set_format_bits(self, mask):
        """
        Sets the format bits for the QR code, which include the error correction level and mask pattern.
        Args:
            mask (int): The mask pattern to be applied.

        This method calculates the error correction bits, appends them to the data, and applies an XOR operation with 0x5412 for readability. 
        It then sets the format bits in the appropriate positions on the QR code matrix, including the top left, bottom left, and top right corners, 
        as well as the dark module.
        """
        data = ecl_lookup[self.ecl][1] << 3 | mask # Combines the error correction level and mask pattern into a single byte

        r = int(data)

        for _ in range(10): # Calculates error correction bits
            r = (r <<1) ^ ((r >> 9) * 0x537)
        
        payload = (data << 10 | r) ^ 0x5412 # Appends error correction bits and XORs with 0x5412 for readibility

        # Top left
        for i in range(0, 6):
            self.set_block(8, i, get_bit(payload, i), True)
        self.set_block(8, 7, get_bit(payload, 6), True)
        self.set_block(8, 8, get_bit(payload, 7), True)
        self.set_block(7, 8, get_bit(payload, 8), True)
        for i in range(9, 15):
            self.set_block(14 - i, 8, get_bit(payload, i), True)
        
        # Copy in other two blocks
        for i in range(0, 8): # Bottom left
            self.set_block(self.size - 1 - i, 8, get_bit(payload, i), True)
        for i in range(8, 15): # Top right
            self.set_block(8, self.size - 15 + i, get_bit(payload, i), True)

        self.set_block(8, self.size - 8, 1, True) # Dark module

    def set_version_bits(self):
        """
        Sets the version bits for the QR code.

        This method calculates the version information bits and places them in the appropriate positions
        in the QR code matrix. The version information is encoded using a BCH code.

        Args:
            None

        Returns:
            None
        """
        r = self.version

        for _ in range(12):
            r = (r << 1) ^ ((r >> 11) * 0x1F25) # Calculates BCH encoding

        payload = self.version << 12 | r # Combines the version number and BCH encoding

        for i in range(18):
            val = get_bit(payload, i)

            a = self.size - 11 + i % 3
            b = i // 3

            self.set_block(a, b, val, True)
            self.set_block(b, a, val, True)

    def prepare_payload(self, data, verbosity = 4):
        """
        Prepares the payload for QR code generation by dividing the data into piles and adding error correction bytes.
        Args:
            data (list): The data to be encoded, represented as a list of bytes.
        Returns:
            list: The interleaved data piles with error correction bytes included.
        """

        num_ec_piles = get_num_ec_piles(self.version, self.ecl) # n° of data piles (data + error correction)
        ec_bytes_len = get_ecp_per_pile(self.version, self.ecl) # n° of error correction bytes per pile
        num_raw_bytes = get_num_data_bytes(self.version) // 8 # n° of raw data bytes

        num_short_piles = num_ec_piles - num_raw_bytes % num_ec_piles # n° of "short" piles (with one less byte)
        short_pile_len = num_raw_bytes // num_ec_piles # Length of the "short" pile

        console_log(f'N° of data piles: {num_ec_piles}\nN° of error correction bytes per pile: {ec_bytes_len}\nN° of raw data bytes: {num_raw_bytes}\nN° of short piles: {num_short_piles}\nLength of short pile: {short_pile_len}', 'info', verbosity, 4)

        piles = [] # Initializing the list of piles

        rs = RSEncoder(ec_bytes_len) # Initializing the Reed-Solomon encoder

        k = 0 # Initializing the index for the data

        for i in range(num_ec_piles):
            pile = data[slice(k, k + short_pile_len - ec_bytes_len + (0 if i < num_short_piles else 1))] # Extracting the pile (with extra data for long piles)


            console_log(f'Pile {i} (before padding): {stringify_bytearray(pile)} (len={len(pile)})', 'info', verbosity, 4)

            k += len(pile) # Updating the index


            ecp = rs.remainder(pile) # Calculating the error correction pile

            if i < num_short_piles:
                pile.append(0) # Adding a dummy byte for short piles

            console_log(f'Pile {i} (after padding): {stringify_bytearray(pile)} (len={len(pile)})', 'info', verbosity, 4)

            piles.append(pile + ecp) # Appending the pile to the list

        console_log(f'Piles successfully prepared!', 'success', verbosity, 3)
        for idx, p in enumerate(piles):
            console_log(f'Pile {idx}: {stringify_bytearray(p)}', 'info', verbosity, 4)
        
        return interleave_data(piles, short_pile_len, ec_bytes_len, num_short_piles, verbosity)

    def set_data_bytes(self, verbosity = 0):
        """
        Sets the data bytes into the QR code matrix.
        This method iterates over the QR code matrix in a specific pattern to place the data bits
        into the appropriate positions. It skips function patterns and ensures the data is placed
        correctly according to the QR code specifications.
        Args:
            None
        """
        
        i = 0 # Index for the payload

        for x in range(self.size - 1, 0, -2): # Keeps track of the right column
            if x <= 6: # At x = 6 there's the timing pattern
                x -= 1 # Offset by one on the left

            for y in range(self.size): # Keeps track of the vertical position
                for j in range(2): # Loops over the two columns of the byte
                    posx = x - j # Actual x position
                    up = (x + 1) & 2 == 0 # Checks if we're traversing the columns from bottom to top or vice versa
                    posy = (self.size - 1 - y) if up else y # Actual y position
                    

                    if not self.isfunction[posy][posx] and i < len(self.payload) * 8:
                        console_log(f'Setting block at ({posx}, {posy}) with value {get_bit(self.payload[i // 8], i % 8)} (index = {i}, payload = {self.payload[i // 8]:08b})', 'info', verbosity, 5)
                        self.set_block(posx, posy, get_bit(self.payload[i // 8], 7 - (i % 8)))
                        i += 1
                    else:
                        console_log(f'Skipping block at ({posx}, {posy}) because {"it is a function block" if self.isfunction[posy][posx] else "the payload is exhausted"}', 'info', verbosity, 5)
    
    def apply_mask(self, mask_index):
        """
        Applies a mask to the QR code blocks based on the specified mask index.
        
        Args:
            mask_index (int): The index of the mask pattern to be applied. 
                      Must be an integer between 0 and 7 inclusive.
        
        The mask is applied to each block in the QR code, except for function patterns.
        """
        mask_collection = {
            0: (lambda x, y: (x + y) % 2 == 0                   ),
            1: (lambda x, y: y % 2 == 0                         ),
            2: (lambda x, y: x % 3 == 0                         ),
            3: (lambda x, y: (x + y) % 3 == 0                   ),
            4: (lambda x, y: (x // 3 + y // 2) % 2 == 0         ),
            5: (lambda x, y:  x * y % 2 + x * y % 3 == 0        ),
            6: (lambda x, y:  (x * y % 2 + x * y % 3) % 2 == 0  ),
            7: (lambda x, y:  ((x + y) % 2 + x * y % 3) % 2 == 0),
        }


        for y in range(self.size):
            for x in range(self.size):
                self.blocks[y][x] ^= mask_collection[mask_index](x, y) and (not self.isfunction[y][x])

    def get_penalty(self, verbosity = 0):
        """
        Calculates the penalty score for the QR code based on various patterns and criteria.
        Args:
            verbosity (int, optional): The verbosity level for logging (default is 0).
        Returns:
            int: The total penalty score calculated from row, column, block, and balance penalties.
        """

        lookup_penalties = [3, 3, 40, 10] # Penalty values for different patterns

        row_res, col_res, block_res, balance_res = 0, 0, 0, 0

        for y in range(self.size):
            row_res += self.get_bar_penalty([self.blocks[y]], lookup_penalties) # Penalty for rows

        console_log(f'Row penalty: {row_res}', 'info', verbosity, 5)

        for x in range(self.size):
            col_res += self.get_bar_penalty([self.blocks[y][x] for y in range(self.size)], lookup_penalties) # Penalty for columns
        
        console_log(f'Column penalty: {col_res}', 'info', verbosity, 5)

        block_res += self.get_square_penalty(lookup_penalties) # Penalty for 2x2 blocks

        console_log(f'Block penalty: {block_res}', 'info', verbosity, 5)

        balance_res += self.get_balance_penalty(lookup_penalties) # Penalty for dark module balance

        console_log(f'Balance penalty: {balance_res}', 'info', verbosity, 5)

        return row_res + col_res + block_res + balance_res

    def get_bar_penalty(self, array, penalties):
        """
        Calculates the penalty score for a given row/column of the QR code, combining both straight line and finder-like penalties.
        Args:
            array (list): A list representing the row or column of the QR code.
            penalties (list): A list of penalty values for different QR code patterns.
        Returns:
            int: The total penalty score for the given array.
        """

        def check_finder_like(array):
            """
            Checks if the given array represents a finder-like pattern.
            Args:
                array (list of tuples): A list representing a summary of a row or column of the QR code.

            Returns:
                bool: True if the array represents a finder-like pattern, False otherwise.
            """
            if len(array) != 7:
                raise ValueError("Invalid array length")
        
            n = array[3][1] // 3 # Setting proportion base
            return ((array[0][1] >= n and array[6][1] >= n)
                    and (array[2][1] == array[4][1] == n)
                    and (array[1][1] == array[5][1] == n)) # Verifying the proportions of a finder-like pattern

        subres = 0

        hist = [] # Initializing the history of the row/column
        active_color = array[0] # Initializing the active color
        streak = 1 # Initializing the streak

        if active_color:
            hist += [(0, self.size)] # If the first element is black, add a dummy white streak
        else:
            streak += self.size # Otherwise, increase the streak by a full row/column

        for i in range(1, len(array)): # Cycle through the array
            if array[i] == active_color:  # If the color doesn't change, increase the streak
                streak += 1
            else:
                hist += [(active_color, streak)] # Otherwise, add the streak to the history, reset active_color and streak
                active_color = array[i]
                streak = 1
        
        for record in hist: # Cycle through the history

            if record[1] >= 5: # Add penalties for streaks of 5 or more
                subres += penalties[0] + (record[1] - 5)
            
        for i in range(len(hist) - 6):
            if hist[i][0] == hist[i + 2][0] == hist[i + 4][0] == hist[i + 6][0] == 0 and hist[i + 1][0] == hist[i + 3][0] == hist[i + 5][0] == 1: # Checking the structure of the finder-like pattern
                subres += check_finder_like(hist[i:i+7]) * penalties[2] # Add penalties for finder-like patterns

        return subres
            
    def get_square_penalty(self, penalties):
        """
        Calculates the square penalty for the QR code based on the given penalties.

        Args:
            penalties (list): A list of penalty scores where penalties[2] is the penalty for 2x2 blocks of the same color.

        Returns:
            int: The total square penalty score.
        """

        subres = 0

        for y in range(self.size - 1):
            for x in range(self.size - 1):
                if (self.blocks[y][x] == self.blocks[y][x + 1] == self.blocks[y + 1][x] == self.blocks[y + 1][x + 1]):
                    subres += penalties[2]

        return subres

    def get_balance_penalty(self, penalties):
        """
        Calculates the balance penalty for the QR code based on the proportion of dark modules.

        Args:
            penalties (list): A list of penalty scores for different conditions.

        Returns:
            int: The calculated balance penalty.
        """

        num_dark = sum(sum(row) for row in self.blocks)
        num_total = self.size ** 2

        dark_ratio = num_dark / num_total

        k = 0

        while dark_ratio < 0.45 - (k * 0.05) or dark_ratio > 0.55 + (k * 0.05): # Calculate the balance penalty
            k += 1

        return penalties[3] * k


###############    Helper functions to QR class    ###############

def pad_and_terminate(data, version, ecl):
    """
    Pads and terminates the given data according to the QR code specifications.
    Args:
        data (str): The data to be encoded in the QR code.
        version (int): The version of the QR code (1 to 40).
        ecl (str): The error correction level. Must be one of 'L', 'M', 'Q', 'H'.
    Returns:
        bytes: The padded and terminated data as a byte array.
    """

    byte_data = BitStream() # Initializing the bit stream

    byte_data.append_bits(byte_mode.modebits, 4) # Appending byte mode indicator

    byte_data.append_bits(len(data), byte_mode.get_num_char_count_bits(version)) # Appending the length of the data

    for char in data:
        byte_data.append_bits(ord(char), 8)

    capacity = get_capacity(version, ecl) * 8

    byte_data.append_bits(0, min(4, capacity - len(byte_data))) # Adding padding bits (up to 4)
    byte_data.append_bits(0, - len(byte_data) % 8) # Aligning to byte boundary (final length of data must be a multiple of 8)


    i = 0
    alternated_padding = [0xEC, 0x11] # Fill up to capacity with alternated padding
    while len(byte_data) < capacity: 
        byte_data.append_bits(alternated_padding[i % 2], 8)
        # print(f'adding padding: {alternated_padding[i % 2]}')
        i += 1
    
    result = byte_data.convert_to_bytes()

    return result

def get_capacity(version, ecl):
    """
    Calculates the capacity of a QR code based on its version and error correction level (ECL).
    
    Args:
        version (int): The version of the QR code (1 to 40).
        ecl (str): The error correction level. Must be one of 'L', 'M', 'Q', 'H'.
    
    Returns:
        int: The capacity of the QR code in bytes.
    """
    return (get_num_data_bytes(version) // 8) - get_ecp_per_pile(version, ecl) * get_num_ec_piles(version, ecl)

def get_num_data_bytes(version):
    """
    Calculates the number of data + EC bytes available for a given QR code version.
    Args:
        version (int): The version of the QR code (must be between 1 and 40 inclusive).
    Returns:
        int: The number of data bytes available for the specified QR code version.
    """
    if version < 1 or version > 40:
        raise ValueError("Invalid version")
    
    res = (((16 * version) + 128) * version) + 64

    if version >= 2: # subtract blocks occupied by alignment patterns
        num_align_patterns = (version // 7) + 2
        res -= (((25 * num_align_patterns) - 10) * num_align_patterns) - 55
        if version >= 7: # subtract blocks occupied by version information
            res -= 36
    
    return res

def get_ecp_per_pile(version, ecl): 
    """
    Retrieves the error correction bytes per block for a given QR code version and error correction level.
    Args:
        version (int): The version of the QR code (1 to 40).
        ecl (str): The error correction level. Must be one of 'L', 'M', 'Q', 'H'.
    Returns:
        int: The number of error correction bytes per block for the specified version and error correction level.
    """

    lookup_table = ( 		# Version:
		# 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40    Error correction level
		(7,  10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),   # (L)ow
		(10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28),  # (M)edium
		(13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),  # (Q)uartile
		(17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30))  # (H)igh
    
    return lookup_table[ecl_lookup[ecl][0]][version - 1]

def get_num_ec_piles(version, ecl):
    """
    Returns the number of error correction bytes per data pile for a given QR code version and error correction level.
    Args:
        version (int): The version of the QR code (1 to 40).
        ecl (str): The error correction level. Must be one of 'L', 'M', 'Q', 'H'.
    Returns:
        int: The number of error correction codewords per block for the specified version and error correction level.
    """
    lookup_table = (
        # Version
		# 1, 2, 3, 4, 5, 6, 7, 8, 9,10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40    Error correction level
		(1, 1, 1, 1, 1, 2, 2, 2, 2, 4,  4,  4,  4,  4,  6,  6,  6,  6,  7,  8,  8,  9,  9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25),  # (L)ow
		(1, 1, 1, 2, 2, 4, 4, 4, 5, 5,  5,  8,  9,  9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49),  # (M)edium
		(1, 1, 2, 2, 4, 4, 6, 6, 8, 8,  8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68),  # (Q)uartile
		(1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81))  # (H)igh
    
    return lookup_table[ecl_lookup[ecl][0]][version - 1]

def interleave_data(piles, short_pile_len, n_ec_bytes_per_pile, n_short_piles, verbosity):
    """
    Interleaves data from multiple piles into a single bytearray, skipping padding bytes in short piles.
    Args:
        piles (list of bytearray): A list of bytearrays, each representing a pile of data.
        short_pile_len (int): The length of the shorter piles.
        n_ec_bytes_per_pile (int): The number of error correction bytes per pile.
        n_short_piles (int): The number of short piles.
    Returns:
        bytearray: A bytearray containing the interleaved data from all piles.
    """
    res = bytearray() # initialize resulting array

    for i in range(len(piles[0])): # appending element i of every pile
        for j, pile in enumerate(piles):
            if (i != short_pile_len - n_ec_bytes_per_pile) or (j >= n_short_piles): # skipping padding byte in short piles
                res.append(pile[i])
    
    console_log(f'Piles successfully interleaved!', 'success', verbosity, 4)

    return res

###############    QR generation wrapper function    ###############


def genqr(data, minversion, maxversion, ecl, verbosity = 0):
    """
    Generates a QR code using the provided data and parameters.

    Args:
        data (str): The data to be encoded in the QR code.
        minversion (int): The minimum version of the QR code.
        maxversion (int): The maximum version of the QR code.
        ecl (str): The error correction level for the QR code.

    Returns:
        QR: An instance of the QR class representing the generated QR code.
    """

    qr = QR(data, minversion, maxversion, ecl, -1, verbosity)

    return qr