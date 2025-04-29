from __future__ import annotations # Depending on your version of python
import time
import threading
import platform
from queue import Queue, Empty

#from api import IMU
#from api import PressureSensor
from api import MotorController
#from api import Indicator
from api import MockController
from api import GPS

from time import sleep
import config
from core import websocket_thread, Navigation, Control
from custom_types import State, Log, SerialState


def main_log(logging_queue:Queue, base_queue:Queue):
    thing = 0
    while(logging_queue.qsize() > 0):
        try:
            thing += 1
            message: Log|str = logging_queue.get_nowait()
            if message:
                if isinstance(message, Log): # If it is just a string, do nothing
                    if message.type == "state" and isinstance(message.content, State): # If type is state, unpack the numpy arrays
                        serial_state = SerialState(
                            position = message.content.position.tolist(),
                            velocity = message.content.velocity.tolist(),
                            #local_velocity = message.content.local_velocity.tolist(),
                            local_force = message.content.local_force.tolist(),
                            attitude = message.content.attitude.tolist(),
                            angular_velocity = message.content.angular_velocity.tolist(),
                            local_torque = message.content.local_force.tolist(),
                            #forward_m_input = float(message.content.forward_m_input),
                            #turn_m_input = float(message.content.turn_m_input)
                        )
                        message.content = serial_state
                    # Since message: Log, we must convert Log to JSON
                    message = message.model_dump_json()
                base_queue.put(message)
                print("LOG: " + str(message))
        except Empty:
            return  

if __name__ == "__main__":
    # This event is set so that all the threads know to end
    stop_event = threading.Event()

    # Anything put into this queue will be printed
    # to stdout & forwarded to frontend
    logging_queue = Queue()

    # Used for thread cleanup
    threads = []

    # Websocket Initialization
    queue_to_base = Queue()
    queue_to_auv = Queue()
    ws_shutdown_q = Queue() # This just takes the single shutdown method for the websocket server
    websocket_thread = threading.Thread(
            target=websocket_thread,
            kwargs={'stop_event':stop_event,
                    'logging_event':logging_queue,
                    'websocket_interface': config.SOCKET_IP,
                    'websocket_port': config.SOCKET_PORT,
                    'ping_interval': config.PING_INTERVAL,
                    'queue_to_base': queue_to_base,
                    'queue_to_auv': queue_to_auv,
                    'verbose': True,
                    'shutdown_q': ws_shutdown_q})
    threads.append(websocket_thread)
    websocket_thread.start()
    ws_shutdown = ws_shutdown_q.get(block=True) # Needed to shut down server

    motor_controller = MotorController()
    #if platform.system() == "Darwin":
        #motor_controller = MockController()

    # Control System Initialization
    queue_input_nav = Queue() # Input from user & state input to nav
    queue_input_control = Queue() # State input to nav
    queue_nav_to_control = Queue() # Setpoint input to nav
    navigation_thread = Navigation(
            input_state_q=queue_input_nav,
            desired_state_q=queue_nav_to_control,
            logging_q=logging_queue,
            stop_event=stop_event
    )
    control_thread = Control(
            input_state_q=queue_input_control,
            desired_state_q=queue_nav_to_control,
            logging_q=logging_queue,
            controller=motor_controller,
            stop_event=stop_event
    )

    """
    gps_queue=Queue()
    gps_thread = GPS(
        out_queue=gps_queue,
        path=config.GPS_PATH,
        stop_event=stop_event
    )
    """

    print("Beginning main loop")
    try:
        while True:
            main_log(logging_queue, queue_to_base)

            try:
                message_from_base = queue_to_auv.get_nowait()
                # Based on commands, execute functions and/or subroutines
                if message_from_base:
                    print("Message from base: " + str(message_from_base))
                    command = message_from_base["command"]
                    if command == "pidConstants":
                        print("Setting PID Constants")
                    elif command == "motorTest":
                        print("Starting motor test")
                        # motor_test = threading.Thread(motor_test)
                        # motor_test.start()
                        try:
                            motor_controller.update_motor_speeds(message_from_base["content"])
                            print(message_from_base["content"])
                        finally:
                            sleep(10)
                            motor_controller.zero_out_motors();

                        # Override control & nav thread
                        # go directly to MC

                    elif command == "headingTest":
                        print("Starting heading test")
                        # TODO: Make heading test a function w/ args
                        # heading_test = Heading_Test()
                        # heading_test.start()

                        # Override nav thread
                        # go directly to control thread

                    elif command == "mission":
                        print("Beginning mission")
                        goal_coordinate = message_from_base["content"]
                        print("Goal: " + str(goal_coordinate))
                        if not navigation_thread.is_alive():
                            threads.append(navigation_thread)
                            navigation_thread.start()
                            threads.append(control_thread)
                            control_thread.start()
                        queue_input_nav.put(goal_coordinate)

            except Empty:
                pass

    except KeyboardInterrupt:
        stop_event.set()
        print("Joining threads")
        ws_shutdown()
        for thread in threads:
            if thread.is_alive():
                thread.join
        print("All threads joined, process exiting")
