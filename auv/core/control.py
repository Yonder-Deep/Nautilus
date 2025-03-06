from queue import Queue

def control(input_state=Queue, desired_state=Queue):
    """ This low-level navigation thread is meant to take as input
        the current state and desired state of the submarine, and
        write to motor controller in order to keep the system
        critically damped so that the error between the current state
        and desired state is minimized.
    """
    pass