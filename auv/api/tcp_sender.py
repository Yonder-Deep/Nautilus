import time
import collections
from static import global_vars
from static import constants


# maybe we won't use this
# in order to implement a TCP-like protocol, we'd need to change the serial timeout to not be 0
# which seems like it may cause issues
class TCPSender:
    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(filepath, "rb")
        self.ack_num = 0
        self.prev_packets = collections.deque(maxlen=15)

    def get_packet(self):
        data = self.file.read(constants.FILE_SEND_PACKET_SIZE - 4)
        header = self.ack_num << (constants.FILE_SEND_PACKET_SIZE - 4)*8
        packet = header | data
        self.prev_packets.append(packet)
        return packet
