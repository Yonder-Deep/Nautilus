from websockets.sync.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
import json
from queue import Queue, Empty
import time
import functools
import threading

def socket_handler(base_websocket=ServerConnection, stop_event=threading.Event, ping_interval=int, queue_to_base=Queue, queue_to_auv=Queue, log=object):
    log("New websocket connection from base")
    log("stop_event" + str(stop_event))
    base_websocket.send("Hello from AUV")
    time_since_last_ping = 0
    while True:
        log("Websocket loop")
        if stop_event.is_set():
            log("Websocket stop event")
            base_websocket.close()
        time.sleep(1)

        try:
            message_from_base = json.loads(base_websocket.recv(timeout=0)) # Doesn't block since timeout=0
            if message_from_base:
                log("Message from base: " + str(message_from_base))
                queue_to_auv.put(message_from_base)
                # Send acknowledgement back to base
                message_from_base["ack"] = True 
                queue_to_base.put(json.dumps(message_from_base))
        except TimeoutError:
            log("Timeout")
        except ConnectionClosedOK:
            log("Base disconnected (OK)")
            return
        except ConnectionClosedError as err:
            log("Base disconnected (ERROR)")
            log(str(err))
            return

        try:
            message_to_base = queue_to_base.get(block=False)
            if message_to_base:
                base_websocket.send(json.dumps(message_to_base))
        except Empty:
            log("Empty")
        except ConnectionClosedOK:
            log("Base disconnected (OK)")
            return
        except ConnectionClosedError as err:
            log("Base disconnected (ERROR)")
            log(str(err))
            return
            
        if time_since_last_ping > ping_interval:
            log("Sending Pong")
            time_since_last_ping=0
            base_websocket.send(json.dumps('pong'))
        else:
            time_since_last_ping += 1

def custom_log(message=str, verbose=bool, queue=Queue):
    if verbose:
        queue.put("Websocket Handler: " + message)

def server(stop_event=threading.Event, logging_event=threading.Event, websocket_interface=str, websocket_port=int, ping_interval=int, queue_to_base=Queue, queue_to_auv=Queue, verbose=bool):
    print("AUV websocket server is alive")
    """ Partially initialize these functions so that the socket handler
        be passed as a single callable to the serve() function
    """
    initialized_logger = functools.partial(custom_log, verbose=verbose, queue=logging_event)
    initialized_handler = functools.partial(socket_handler, stop_event=stop_event, ping_interval=ping_interval, queue_to_base=queue_to_base, queue_to_auv=queue_to_auv, log=initialized_logger)
    with serve(initialized_handler, host=websocket_interface, port=websocket_port, origins=None) as server:
        server.serve_forever()