from typing import Union, Literal, Callable, Optional
import multiprocessing
import multiprocessing.queues
import threading
import queue
from msgspec import Struct
from abc import ABC as abc, abstractmethod
from time import sleep

def or_set(self):
    self._set()
    self.changed()

def or_clear(self):
    self._clear()
    self.changed()

def orify(e, changed_callback):
    e._set = e.set
    e._clear = e.clear
    e.changed = changed_callback
    e.set = lambda: or_set(e)
    e.clear = lambda: or_clear(e)

def multi_event(*events):
    or_event = threading.Event()
    def changed():
        bools = [e.is_set() for e in events]
        if any(bools):
            or_event.set()
        else:
            or_event.clear()
    for e in events:
        orify(e, changed)
    changed()
    return or_event
 
class TaskInfo(Struct):
    name: str
    type: Union[Literal["Process"], Literal["Thread"]]
    input_q: Union[multiprocessing.queues.Queue, queue.Queue]
    started_event: Union[multiprocessing.Event, threading.Event] # type: ignore
    enabled_event: Union[multiprocessing.Event, threading.Event] # type: ignore
    started: bool = False

def make_task(task_type: Literal["Process", "Thread"]):
    if task_type == "Process":
        base = multiprocessing.Process
        make_queue = multiprocessing.Queue
        make_event = multiprocessing.Event
    elif task_type == "Thread":
        base = threading.Thread
        make_queue = queue.Queue
        make_event = threading.Event
    else:
        raise TypeError("Task must be of type process or thread")

    class Task(base): # type: ignore
        def __init__(self, name: str):
            super().__init__(name=name)
            self.meta = TaskInfo(
                name=name,
                type=task_type,
                input_q=make_queue(), # type: ignore
                started_event=make_event(), # type: ignore
                enabled_event=make_event(), # type: ignore
                started=False,
            )
            
        def run(self):
            """ Don't call super().run() to run this (override it instead).
                This is just for testing purposes.

                ## There are a few possiblities when the events are set:

                stop_event gets set:
                * start() has not been called
                    -> don't let this happen
                * start() has been called but disable_event is set
                    -> exit run()
                * start() has been called and the loop is running
                    -> exit run()

                disable_event gets set:
                * start() has not been called
                    -> when start() called, wait until disable_event is cleared
                * start() has been called but stop_event is set
                    -> should already be exiting exit run()
                * start() has been called and the loop is running
                    -> wait until disable_event is cleared
            """
            meta = self.meta
            def log(x: str):
                print(self.meta.name + ": " + x)
            while True:
                if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                    log("Some event is set")
                    if not meta.enabled_event.is_set():
                        log("enabled_event is clear, task disabled")
                        meta.enabled_event.wait()
                    if not meta.started_event.is_set():
                        log("started_event is clear, task finishing")
                        break;
                sleep(1)
                log("Alive")

        def startup(self):
            self.meta.started = True
            self.meta.started_event.set()
            self.start()

        def shutdown(self) -> bool:
            """ If the task has been started already, it cannot be shutdown and
                this method will return `False`. Otherwise, it will return `True`.
            """
            if self.meta.started:
                self.meta.enabled_event.set()
                self.meta.started_event.clear()
                return True
            else:
                return False

        def activate(self):
            self.meta.enabled_event.set()

        def deactivate(self):
            self.meta.enabled_event.clear()

        def input(self, x):
            self.meta.input_q.put(x)

    return Task

class YonderProcess(multiprocessing.Process): # type: ignore
    def __init__(self, name: str):
        super().__init__(name=name)
        self.meta = TaskInfo(
            name=name,
            type="Process",
            input_q=multiprocessing.Queue(), # type: ignore
            started_event=multiprocessing.Event(), # type: ignore
            enabled_event=multiprocessing.Event(), # type: ignore
            started=False,
        )
        
    def run(self):
        """ Don't call super().run() to run this (override it instead).
            This is just for testing purposes.

            ## There are a few possiblities when the events are set:

            stop_event gets set:
            * start() has not been called
                -> don't let this happen
            * start() has been called but disable_event is set
                -> exit run()
            * start() has been called and the loop is running
                -> exit run()

            disable_event gets set:
            * start() has not been called
                -> when start() called, wait until disable_event is cleared
            * start() has been called but stop_event is set
                -> should already be exiting exit run()
            * start() has been called and the loop is running
                -> wait until disable_event is cleared
        """
        meta = self.meta
        def log(x: str):
            print(self.meta.name + ": " + x)
        while True:
            if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                log("Some event is set")
                if not meta.enabled_event.is_set():
                    log("enabled_event is clear, task disabled")
                    meta.enabled_event.wait()
                if not meta.started_event.is_set():
                    log("started_event is clear, task finishing")
                    break;
            sleep(1)
            log("Alive")

    def startup(self):
        self.meta.started = True
        self.meta.started_event.set()
        self.start()

    def shutdown(self) -> bool:
        """ If the task has been started already, it cannot be shutdown and
            this method will return `False`. Otherwise, it will return `True`.
        """
        if self.meta.started:
            self.meta.enabled_event.set()
            self.meta.started_event.clear()
            return True
        else:
            return False

    def activate(self):
        self.meta.enabled_event.set()

    def deactivate(self):
        self.meta.enabled_event.clear()

    def input(self, x):
        self.meta.input_q.put(x)

if __name__ == "__main__":
    print("--------\nThread\n--------")
    def log(x: str):
        print("Main: " + x)
    thd = YonderThread("Test-Thread-1")
    log(f"Calling startup() on {thd.meta.name}")
    thd.startup()
    log(f"Calling activate() on {thd.meta.name}")
    thd.activate()
    delay = 3
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling deactivate() on {thd.meta.name}")
    thd.deactivate()
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling activate() on {thd.meta.name}")
    thd.activate()
    delay = 3
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling shutdown() on {thd.meta.name}")
    thd.shutdown()
    log(f"Calling join() on {thd.meta.name}")
    thd.join()
    log("Finished")
    print("--------\nProcess\n--------")
    pcs = YonderProcess("Test-Process-1")
    log(f"Calling startup() on {pcs.meta.name}")
    pcs.startup()
    log(f"Calling activate() on {pcs.meta.name}")
    pcs.activate()
    delay = 3
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling deactivate() on {pcs.meta.name}")
    pcs.deactivate()
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling activate() on {pcs.meta.name}")
    pcs.activate()
    delay = 3
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling shutdown() on {pcs.meta.name}")
    pcs.shutdown()
    log(f"Calling join() on {pcs.meta.name}")
    pcs.join()
    log("Finished")
