try:
    import sys
    sys.path.append("..")
    from data_types import State 
except:
    from .data_types import State 

import numpy as np
from multiprocessing import shared_memory, Process


def create_shared_state(name: str) -> shared_memory.SharedMemory:
    data_type = np.float64
    num_elements_per_array = 3
    num_arrays = 4
    total_elements = num_elements_per_array * num_arrays
    total_bytes = total_elements * np.dtype(data_type).itemsize
    # Create shared memory
    shm = shared_memory.SharedMemory(create=True, size=total_bytes, name=name)
    # Create initial NumPy array views in the master process
    array1_offset = 0
    array2_offset = np.dtype(data_type).itemsize * num_elements_per_array
    array3_offset = np.dtype(data_type).itemsize * num_elements_per_array * 2
    array4_offset = np.dtype(data_type).itemsize * num_elements_per_array * 3

    master_array1 = np.ndarray((num_elements_per_array,), dtype=data_type, buffer=shm.buf, offset=array1_offset)
    master_array2 = np.ndarray((num_elements_per_array,), dtype=data_type, buffer=shm.buf, offset=array2_offset)
    master_array3 = np.ndarray((num_elements_per_array,), dtype=data_type, buffer=shm.buf, offset=array3_offset)
    master_array4 = np.ndarray((num_elements_per_array,), dtype=data_type, buffer=shm.buf, offset=array4_offset)

    master_array1[:] = [0, 0, 0]
    master_array2[:] = [0, 0, 0]
    master_array3[:] = [0, 0, 0]
    master_array4[:] = [0, 0, 0]
 
    return shm

def write_shared_state(name: str, state: State):
    existing_shm = shared_memory.SharedMemory(name=name)
    data_type = np.float64
    num_elements_per_array = 3

    array1_offset = 0
    array2_offset = np.dtype(data_type).itemsize * num_elements_per_array
    array3_offset = np.dtype(data_type).itemsize * num_elements_per_array * 2
    array4_offset = np.dtype(data_type).itemsize * num_elements_per_array * 3

    shared_array1 = np.ndarray((3,), dtype=data_type, buffer=existing_shm.buf, offset=array1_offset)
    shared_array2 = np.ndarray((3,), dtype=data_type, buffer=existing_shm.buf, offset=array2_offset)
    shared_array3 = np.ndarray((3,), dtype=data_type, buffer=existing_shm.buf, offset=array3_offset)
    shared_array4 = np.ndarray((3,), dtype=data_type, buffer=existing_shm.buf, offset=array4_offset)

    shared_array1[:] = state.position
    shared_array2[:] = state.velocity
    shared_array3[:] = state.attitude
    shared_array4[:] = state.angular_velocity

def read_shared_state(name: str) -> State:
    existing_shm = shared_memory.SharedMemory(name=name)
    data_type = np.float64

    array1_offset = 0
    array2_offset = np.dtype(data_type).itemsize * 3
    array3_offset = np.dtype(data_type).itemsize * 3 * 2
    array4_offset = np.dtype(data_type).itemsize * 3 * 3

    shared_array1 = np.ndarray((3,), dtype=data_type, buffer=existing_shm.buf, offset=array1_offset)
    shared_array2 = np.ndarray((3,), dtype=data_type, buffer=existing_shm.buf, offset=array2_offset)
    shared_array3 = np.ndarray((3,), dtype=data_type, buffer=existing_shm.buf, offset=array3_offset)
    shared_array4 = np.ndarray((3,), dtype=data_type, buffer=existing_shm.buf, offset=array4_offset)

    state = State(
        position=shared_array1.copy(),
        velocity=shared_array2.copy(),
        attitude=shared_array3.copy(),
        angular_velocity=shared_array4.copy(),
    )
    existing_shm.close()
    return state

def test_process(name:str):
    print("Worker process alive")
    print("Reading shared state:")
    readState1 = read_shared_state(name=name)
    print(repr(readState1))
    print("Writing shared state with position[0] = 10.0")
    readState1.position[0] = 10.0
    write_shared_state(name=name, state=readState1)

if __name__ == "__main__":
    print("Initializing shared state")
    name = "test_shared_state"
    shm = create_shared_state(name)
    try:
        p = Process(target=test_process, args=[name])
        p.start()
        p.join()
        print("Reading shared state again:")
        readState2= read_shared_state(name=name)
        print(repr(readState2))
    finally:
        shm.close()
        shm.unlink()
