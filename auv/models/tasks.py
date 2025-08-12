from typing import Union, Literal, Callable, Optional
import multiprocessing
import multiprocessing.queues
import threading
import queue
from msgspec import Struct
from abc import ABC as abc, abstractmethod
from time import sleep

class TaskInfo(Struct):
    name: str
    type: Union[Literal["Process"], Literal["Thread"]]
    input_q: Union[multiprocessing.queues.Queue, queue.Queue]
    logging_q: Union[multiprocessing.queues.Queue, queue.Queue]
    started_event: Union[multiprocessing.Event, threading.Event] # type: ignore
    enabled_event: Union[multiprocessing.Event, threading.Event] # type: ignore
    started: bool = False
    active: bool = False

class Task(abc):
    def __init__(self):
        self.meta: TaskInfo

    @abstractmethod
    def run(self):
        raise NotImplementedError
    @abstractmethod
    def input(self, x):
        raise NotImplementedError

    @abstractmethod
    def loop(self):
        raise NotImplementedError

    @abstractmethod
    def join(self):
        raise NotImplementedError

    @abstractmethod
    def startup(self):
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def activate(self):
        raise NotImplementedError

    @abstractmethod
    def deactivate(self):
        raise NotImplementedError

class TTask(threading.Thread, Task): # type: ignore
    def __init__(self, name: str):
        super().__init__(name=name)
        self.meta = TaskInfo(
            name=name,
            type="Thread",
            input_q=queue.Queue(),
            logging_q=queue.Queue(),
            started_event=threading.Event(),
            enabled_event=threading.Event(),
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
        loop = self.loop
        while True:
            if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                if not meta.enabled_event.is_set():
                    meta.enabled_event.wait()
                if not meta.started_event.is_set():
                    break;
            loop()
    
    def loop(self):
        raise NotImplementedError("You must either override the run() method \
            or the loop() method with custom code")

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
        self.meta.active = True

    def deactivate(self):
        self.meta.enabled_event.clear()
        self.meta.active = False

    def input(self, x):
        self.meta.input_q.put(x)

class PTask(multiprocessing.Process, Task): # type: ignore
    def __init__(self, name: str):
        super().__init__(name=name)
        self.meta = TaskInfo(
            name=name,
            type="Process",
            input_q=multiprocessing.Queue(),
            logging_q=multiprocessing.Queue(),
            started_event=multiprocessing.Event(),
            enabled_event=multiprocessing.Event(),
            started=False,
        )
        
    def run(self):
        meta = self.meta
        loop = self.loop
        while True:
            if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                if not meta.enabled_event.is_set():
                    meta.enabled_event.wait()
                if not meta.started_event.is_set():
                    break;
            loop()
    
    def loop(self):
        raise NotImplementedError("You must either override the run() method \
            or the loop() method with custom code")

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

class ExampleTask(TTask):
    def run(self):
        meta = self.meta
        def log(x: str):
            print(meta.name + ": " + x)
        while True:
            if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                log("Some event is set")
                if not meta.enabled_event.is_set():
                    log("enabled_event is clear, task disabled")
                    meta.enabled_event.wait()
                if not meta.started_event.is_set():
                    log("started_event is clear, task finishing")
                    break;
            sleep(0.5)
            log("Alive")

class ExamplePTask(PTask):
    def run(self):
        meta = self.meta
        def log(x: str):
            print(meta.name + ": " + x)
        while True:
            if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                log("Some event is set")
                if not meta.enabled_event.is_set():
                    log("enabled_event is clear, task disabled")
                    meta.enabled_event.wait()
                if not meta.started_event.is_set():
                    log("started_event is clear, task finishing")
                    break;
            sleep(0.5)
            log("Alive")

if __name__ == "__main__":
    print("--------\nThread\n--------")
    def log(x: str):
        print("Main: " + x)
    thd = ExampleTask("Example-Thread-1")
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
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling shutdown() on {thd.meta.name}")
    thd.shutdown()
    log(f"Calling join() on {thd.meta.name}")
    thd.join()
    log("Finished")
    print("--------\nProcess\n--------")
    pcs = ExamplePTask("Example-Process-1")
    log(f"Calling startup() on {pcs.meta.name}")
    pcs.startup()
    log(f"Calling activate() on {pcs.meta.name}")
    pcs.activate()
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling deactivate() on {pcs.meta.name}")
    pcs.deactivate()
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling activate() on {pcs.meta.name}")
    pcs.activate()
    log(f"Waiting {delay} seconds")
    sleep(delay);
    log(f"Calling shutdown() on {pcs.meta.name}")
    pcs.shutdown()
    log(f"Calling join() on {pcs.meta.name}")
    pcs.join()
    log("Finished")
