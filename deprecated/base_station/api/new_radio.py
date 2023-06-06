"""
The radio class enables communication over wireless serial radios.
"""
import serial
TIMEOUT_DURATION = 0
DEFAULT_BAUDRATE = 115200


class Radio():
    def __init__(self, serial_path, baudrate=DEFAULT_BAUDRATE):
        """
        Initializes the radio object.

        serial_path: Absolute path to serial port for specified device.
        """

        # Establish connection to the serial radio.
        self.ser = serial.Serial(serial_path,
                                 baudrate=baudrate, parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                                 timeout=TIMEOUT_DURATION
                                 )

    def write(self, hex_string):
        """
        Sends provided message over serial connection.

        hex_string: A hexadecimal string that is sent over serial connection.
        """

        if hex_string == 'PING':
            hex_string = "F" # 1111 => ping command

        byte_string = bytes.fromhex(hex_string)
        self.ser.write(byte_string)

    def read_bytes(self):
        """
        Reads all bytes in buffer.
        """
        return self.ser.read(size=self.ser.in_waiting)

    def read(self, n_bytes=1):
        """
        Returns array of bytes
        """
        return self.ser.read(size=n_bytes)

    def is_open(self):
        """
        Returns a boolean if the serial connection is open.
        """
        return self.ser.is_open

    def flush(self):
        """
        Clears the buffer of the serial connection.
        """
        self.ser.flush()

    def close(self):
        """
        Closes the serial connection
        """
        self.ser.close()
