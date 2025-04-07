from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
import json
from queue import Queue, Empty
import time
import threading

# TODO: Ping/Pong heartbeat

def auv_socket_handler(stop_event : threading.Event, ip_address:str, ping_interval:int, queue_to_frontend:Queue, queue_to_auv:Queue):
    print("AUV Socket Handler Alive")
    #with connect(uri=ip_address) as websocket:
    websocket = connect(uri=ip_address)
    hello = websocket.recv(timeout=None)
    print("AUV Hello: ", hello)
    while True:
        if stop_event.is_set():
            websocket.close()
            return
        time.sleep(0.01)

        try:
            message_to_frontend = json.loads(websocket.recv(timeout=0.001)) # Doesn't block since timeout=0
            if message_to_frontend:
                print("Message from AUV: " + message_to_frontend)
                queue_to_frontend.put(message_to_frontend)
        except TimeoutError:
            pass
        except ConnectionClosedOK:
            print("AUV disconnected (OK)")
            return
        except ConnectionClosedError as err:
            print("AUV disconnected (ERROR)")
            print(str(err))
            return

        try:
            message_to_auv = queue_to_auv.get_nowait()
            if message_to_auv:
                websocket.send(json.dumps(message_to_auv))
        except Empty:
            pass
        except ConnectionClosedOK:
            print("AUV disconnected (OK)")
            return
        except ConnectionClosedError as err:
            print("AUV disconnected (ERROR)")
            print(str(err))
            return
