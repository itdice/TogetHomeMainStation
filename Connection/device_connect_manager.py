#
# device_connect_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import socketio
import eventlet
from enum import Enum
from queue import Queue

sio = socketio.Server(async_mode="eventlet")
app = socketio.WSGIApp(sio)


@sio.event
def connect(sid):
    print("--------------------------------------------")
    print(f"Client [{sid}] Connected!!!")
    print("--------------------------------------------")


@sio.event
def disconnect(sid):
    print("--------------------------------------------")
    print(f"Client [{sid}] Disconnected!!!")
    print("--------------------------------------------")


@sio.on("test_send")
def test_send(sid, data):
    print("--------------------------------------------")
    print(f"Client [{sid}] send Data")
    print(f"Data = {data}")
    print("--------------------------------------------")


@sio.on("test_request")
def test_request(sid):
    print("--------------------------------------------")
    print(f"Client [{sid}] request Test Data!!!")
    print("--------------------------------------------")

    floatdata = 1.23456789

    sio.emit('test_response', {'message': 'Test connection from Server',
                               "hex": 0xAABBCCDDEEFF,
                               "int": 123456789,
                               "float": floatdata
                               }, room=sid)

    print("--------------------------------------------")
    print(f"Test Data Send to Client [{sid}]")
    print("--------------------------------------------")


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8710)), app, log_output=False)