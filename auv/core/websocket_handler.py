from websockets.sync.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from models.data_types import Log
from models.tasks import TTask, TaskInfo

import json
from queue import Queue, Empty, Full
import time
import functools
import threading
from typing import Callable

def socket_handler(
        base_websocket:ServerConnection,
        stop_event:threading.Event,
        ping_interval:int,
        queue_to_base:Queue,
        queue_from_base:Queue,
        log:Callable[[str], None],
):
    log("New websocket connection from base")
    base_websocket.send("Hello from AUV")
    """last_ping = time.time()
    time_since_last_ping = 0"""
    while True:
        #log("Websocket loop")
        if stop_event.is_set():
            log("Websocket stop event")
            base_websocket.close()
        time.sleep(0.001)

        try:
            message_from_base = json.loads(base_websocket.recv(timeout=0)) # Doesn't block since timeout=0
            if message_from_base:
                log("Message from base: " + str(message_from_base))
                queue_from_base.put(message_from_base)
                # Send acknowledgement back to base
                message_from_base["ack"] = True 
                queue_to_base.put_nowait(json.dumps(message_from_base))
        except TimeoutError:
            #log("Timeout")
            pass
        except ConnectionClosedOK:
            log("Base disconnected (OK)")
            return
        except ConnectionClosedError as err:
            log("Base disconnected (ERROR)")
            log(str(err))
            return
        except Full:
            pass

        try:
            message_to_base = queue_to_base.get(block=False)
            if message_to_base:
                base_websocket.send(json.dumps(message_to_base))
        except Empty:
            #log("Empty")
            pass
        except ConnectionClosedOK:
            log("Base disconnected (OK)")
            return
        except ConnectionClosedError as err:
            log("Base disconnected (ERROR)")
            log(str(err))
            return
            
def custom_log(message:str, verbose:bool, queue:Queue):
    if verbose:
        queue.put(Log(
            source="WSKT",
            type="text",
            content=message,
        ))

class WebsocketHandler(TTask):
    """ Websocket server that binds to the given network interface & port.
        Anything in queue_to_base will be forwarded into the websocket.
        Anything that shows up in the websocket will be forwarded to queue_from_base.
    """
    def __init__(
        self,
        websocket_interface:str,
        websocket_port:int,
        ping_interval:int,
        queue_to_base:Queue,
        queue_from_base:Queue,
        verbose:bool,
        shutdown_q:Queue,
        logging_q:Queue,
    ):
        super().__init__(name="WebsocketHandler")
        # Overriding self.meta for custom queues
        self.meta = TaskInfo(
            name="WebsocketHandler",
            type="Thread",
            input_q=queue_to_base,
            logging_q=queue_to_base,
            started_event=threading.Event(),
            enabled_event=threading.Event(),
            started=False,
        )
        self.queue_to_base = queue_to_base
        self.queue_from_base = queue_from_base
        self.shutdown_q = shutdown_q
        self.log = functools.partial(custom_log, verbose=verbose, queue=logging_q)
        self.ping_interval = ping_interval
        self.host = websocket_interface
        self.port = websocket_port
    
    # Overriding run() since the websocket isn't a spinloop
    def run(self):
        initialized_handler = functools.partial(
            socket_handler,
            stop_event=self.meta.started_event,
            ping_interval=self.ping_interval,
            queue_to_base=self.queue_to_base,
            queue_from_base=self.queue_from_base,
            log=self.log,
        )
        self.log("AUV websocket server is alive")
        self.log("Hosting on " + self.host + ":" + str(self.port))
        with serve(initialized_handler, host=self.host, port=self.port, origins=None) as server:
            self.shutdown_q.put(server.shutdown)
            server.serve_forever()
