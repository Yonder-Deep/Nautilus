from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

import json
from queue import Queue, Empty
from functools import partial
import threading
from time import time
from typing import Optional, Union, Callable
from dataclasses import dataclass, asdict

@dataclass
class Ping:
    event: Optional[threading.Event]
    init_time: float
    elapsed_time: Optional[float] = None

@dataclass
class Data:
    type: str
    content: Union[Ping, str]
    source: str = "WSKT"

def custom_log(message: str, queue:Queue):
    queue.put("WSKT: \n" + message)
    print("\033[42mWSKT:\033[0m " + message)

def socket_handler(
    stop_event: threading.Event,
    ip_address: str,
    ping_interval: int,
    queue_to_frontend: Queue,
    queue_to_auv: Queue,
    meta_from_frontend: Queue,
    log: Callable,
    connected_event: threading.Event,
):
    last_ping = time() - ping_interval # To do first ping immediately
    active_pings = []
    try:
        websocket = connect(uri=ip_address)
        hello = websocket.recv(timeout=None)
        log("AUV Hello: " + str(hello))
        connected_event.set()
        while True:
            if stop_event.is_set():
                stop_event.clear()
                websocket.close()
                return

            # For any active pings, check if the pong has been received
            for ping in active_pings:
                if ping.event.is_set():
                    ping.elapsed_time = time() - ping.init_time
                    ping.event = None
                    ping_result = Data(
                        type = "ping",
                        content = ping
                    )
                    queue_to_frontend.put(json.dumps(asdict(ping_result)))
                    active_pings.remove(ping)
            
            if time() - last_ping > ping_interval:
                active_pings.append(
                    Ping(
                        event = websocket.ping(),
                        init_time = time()
                    )
                )
                last_ping = time()

            # If ping requested, ping and set up object
            try:
                meta_command = meta_from_frontend.get_nowait()
                log("Received meta command: \n" + json.dumps(meta_command))
                if meta_command["content"] == "ping":
                    event = websocket.ping()
                    new_ping = Ping(
                        event = event,
                        init_time = time()
                    )
                    active_pings.append(new_ping)
            except Empty:
                pass

            # Forward messages from both ends
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
        log(repr(err))
        dead_object = Data(
            type = "WSKT",
            content = "WSKT DEAD"
        )
        log(json.dumps(asdict(dead_object)))
        connected_event.clear()
        return

def socket_thread(
    stop_event: threading.Event,
    ip_address: str,
    ping_interval: int,
    queue_to_frontend: Queue,
    queue_to_auv: Queue,
    meta_from_frontend: Queue,
    restart_event: threading.Event,
    shutdown_event: threading.Event,
    connected_event: threading.Event,
):
    """ stop_event does not stop the thread, it merely closes the websocket
        ping_interval not yet implemented.
        queue_to_frontend and queue_to_auv are the passthrough "pipe" queues
        meta_from_frontend is for websocket ping commands
        restart_event tries to reconnect the websocket
        shutdown_event exits the thread so it can be joined

        Note: to fully end the connection and shut down, both stop_event and
        shutdown_event must be set.
    """
    log = partial(custom_log, queue=queue_to_frontend)
    log("AUV Socket Handler Alive")
    restart_event.set() # To start the first time
    while True:
        if shutdown_event.is_set():
            return
        if restart_event.is_set():
            stop_event.clear()
            restart_event.clear()
            socket_handler(
                stop_event,
                ip_address,
                ping_interval,
                queue_to_frontend,
                queue_to_auv,
                meta_from_frontend,
                log,
                connected_event,
            )
