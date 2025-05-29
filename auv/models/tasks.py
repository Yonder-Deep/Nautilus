from typing import Union, Literal, Callable
import multiprocessing
import multiprocessing.queues
import threading
import queue
import msgspec
 
class Task(msgspec.Struct):
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
    
def task_factory(
        constructor: Callable,
        input_q: Union[multiprocessing.queues.Queue, queue.Queue],
        stop_event: Union[multiprocessing.Event, threading.Event], # type: ignore
        **kwargs,
) -> Task:
    value = constructor(
            stop_event,
            input_q,
            **kwargs,
    )
    if isinstance(value, threading.Thread):
        type = "Thread"
    elif isinstance(value, multiprocessing.Process):
        type = "Process"
    else:
        raise TypeError("Executor constructor must return a Thread or Process object")
    return Task(
            type=type,
            value=value,
            input_q=input_q,
            stop_event=stop_event,
    )
