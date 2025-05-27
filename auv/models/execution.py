from typing import Union, Literal
import multiprocessing
import multiprocessing.queues
import threading
import queue
import msgspec
 
class Executor(msgspec.Struct):
    """ A data class describing an executing piece of python code, wrapping it
        into an easier common data interface over processes and threads.
    """
    type: Union[Literal["Process"], Literal["Thread"]]
    value: Union[multiprocessing.Process, threading.Thread]
    input_q: Union[multiprocessing.queues.Queue, queue.Queue]
    stop_event: Union[multiprocessing.Event, threading.Event] # type: ignore
    started: bool = False
    
    def start(self):
        self.value.start()

    def stop(self):
        self.stop_event.set()

    def input(self, thing):
        self.input_q.put(thing)
