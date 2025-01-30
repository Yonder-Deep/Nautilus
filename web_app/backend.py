from websockets.sync.client import connect
import json
from queue import Queue

# TODO: Ping/Pong heartbeat

def auv_socket_handler(ip_address=str, ping_interval=int, queue_to_frontend=Queue, queue_to_auv=Queue):
    with connect(uri=ip_address, ping_interval=ping_interval) as websocket:
        while True:
            try:
                message_to_frontend = websocket.recv(timeout=0) # Doesn't block since timeout=0
                if message_to_frontend:
                    queue_to_frontend.put(json.load(message_to_frontend))
            finally:
                continue
            try:
                message_to_auv = queue_to_auv.get(block=False)
                if message_to_auv:
                    websocket.send(json.dumps(message_to_auv))
            finally: continue
    
# Async Implementation Experiment: 

#async def receive_messages(websocket=ClientConnection, queue_to_frontend=Queue):
#    async for message in websocket:
#        queue_to_frontend.put(json.loads(message))
#
#async def send_messages(websocket=ClientConnection, queue_to_auv=Queue):
#    while True:
#        data = queue_to_auv.get()
#        await websocket.send(json.dumps(data))
#
#async def handle_websocket(websocket=ClientConnection, queue_to_frontend=Queue, queue_to_auv=Queue):
#    return await asyncio.gather(
#        receive_messages(websocket, queue_to_frontend),
#        send_messages(websocket, queue_to_auv)
#    )
#
#async def backend_routine(ip_address=str, ping_interval=int, queue_to_frontend=Queue, queue_to_auv=Queue):
#    async for websocket in connect(ip_address, ping_interval=ping_interval):
#        try:
#            handlers = handle_websocket(websocket, queue_to_frontend, queue_to_auv)
#            while True:
#                message = queue_to_auv.get();
#
#        except ConnectionClosed:
#            continue