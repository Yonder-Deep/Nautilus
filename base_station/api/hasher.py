"""
Hasher file for checksum communication validation.
"""


def validate_msg(msg, val):
    return generate_checksum(msg) == val


def generate(msg):
    # TODO - generate the checksum of our message
    return None

# cmd = "some command"
# msg_dict = {"command": encoded_cmd, "csum": checksum}
# encode msg_dict
# send over serial connection
# decode
#
# step 1: encode command
# step 2: generate checksum
# step 3: store into dict and encode dict
# step 4: send encoded dict over connection
# step 5: decode dict
# step 6: recalculate checksum
# step 7: compare checksum with what was read in
# step 8: validate
# step 9: decode cmd
# step 10: use command!
