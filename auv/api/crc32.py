crc_divisor = 0x104c11db7


class Crc32():

    # add checksum to exporting message
    def generate(message):
        # shift to leave room for remainder
        message = message << (32)
        # calculate remainder
        remainder = message % crc_divisor
        # add remainder
        message = message + (crc_divisor - remainder)

        return message

    # check is the crc32 bit
    def confirm(message):
        if message % crc_divisor == 0:
            return True
        else:
            return False