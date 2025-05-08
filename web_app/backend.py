from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
import json
from queue import Queue, Empty
from functools import partial
import threading

# TODO: Ping/Pong heartbeat

def custom_log(message: str, queue:Queue):
    queue.put(message)
    print("\033[42mWSKT:\033[0m " + message)

def auv_socket_handler(stop_event : threading.Event, ip_address:str, ping_interval:int, queue_to_frontend:Queue, queue_to_auv:Queue):
    log = partial(custom_log, queue=queue_to_frontend)
    log("AUV Socket Handler Alive")
    #with connect(uri=ip_address) as websocket:
    try:
        websocket = connect(uri=ip_address)
        hello = websocket.recv(timeout=None)
        log("AUV Hello: " +  str(hello))
        while True:
            if stop_event.is_set():
                websocket.close()
                return

            try:
                message_to_frontend = json.loads(websocket.recv(timeout=0.0001)) # Doesn't block since timeout=0
                if message_to_frontend:
                    queue_to_frontend.put(message_to_frontend)
            except TimeoutError:
                pass
            try:
                message_to_auv = queue_to_auv.get_nowait()
                if message_to_auv:
                    websocket.send(json.dumps(message_to_auv))
            except Empty:
                pass


    except Exception as err:
        if err.__class__ == ConnectionClosedOK:
            log("AUV disconnected (OK)")
        elif err.__class__ == ConnectionClosedError:
            log("AUV disconnected (ERROR)")
        else:
            log("Unknown error")
        log(str(err))
        return
