"""
The radio class enables communication over wireless serial radios.
"""
import serial
from .crc32 import Crc32
TIMEOUT_DURATION = 0
#DEFAULT_BAUDRATE = 115200
DEFAULT_BAUDRATE = 57600


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

    def write(self, message):
        """
        Sends provided message over serial connection.

        message: A string message that is sent over serial connection.
        """
        # Process different types of messages
        if isinstance(message, str):
            encoded = str.encode(message + "\n")
            self.ser.write(encoded)

        elif isinstance(message, int):

            # print("bytes written")
            message = Crc32.generate(message)
            byte_arr = message.to_bytes(7, 'big')
            self.ser.write(byte_arr)

    def readlines(self):
        """
        Returns an array of lines
        """
        lines = self.ser.readlines()
        return [line.decode('utf-8').replace("\n", "") for line in lines]

    def read_bytes(self):
        """
        Reads all bytes in buffer.
        """
        return self.ser.read(self.ser.in_waiting)

    def read(self, n_bytes=1):
        """
        Returns array of bytes
        """
        return self.ser.read(n_bytes)

    def readline(self):
        """
        Returns a string from the serial connection.
        """
        return self.ser.readline().decode('utf-8').replace("\n", "")

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
