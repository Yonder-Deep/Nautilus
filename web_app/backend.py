from websockets.sync.client import connect
import json
from queue import Queue

# TODO: Ping/Pong heartbeat

def auv_socket_handler(ip_address=str, ping_interval=int, queue_to_frontend=Queue, queue_to_auv=Queue):
    with connect(uri=ip_address, ping_interval=ping_interval) as websocket:
        while True:
            try:
                message_to_frontend = websocket.recv(timeout=0) # Doesn't block since timeout=0
                if message_to_frontend:
                    queue_to_frontend.put(json.load(message_to_frontend))
            finally:
                pass
            try:
                message_to_auv = queue_to_auv.get_nowait()
                if message_to_auv:
                    websocket.send(json.dumps(message_to_auv))
            finally:
                pass