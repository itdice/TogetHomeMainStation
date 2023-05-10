#
# device_connect_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import sys
import os
import threading
import eventlet
import socketio
from queue import Queue

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))  # Master Path Finder
from Database import db_manager

# Device Connect Part
sio = socketio.Server(async_mode="eventlet")
app = socketio.WSGIApp(sio)

# DB Manger Part
db_tx_queue = Queue(maxsize=4096)
db_rx_queue = Queue(maxsize=4096)
db_connector = db_manager.DatabaseManagerSystem(db_tx_queue, db_rx_queue)
db_thread = threading.Thread(target=db_connector.startup, args=())
db_thread.daemon = True
db_thread.start()


@sio.event
def connect(sid, environ):
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
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] request Test Data!!!")
    print("--------------------------------------------------------------")

    tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.DEVICE, {})
    db_tx_queue.put(tx_ticket.key)
    rx_ticket = db_connector.wait_to_return(tx_ticket.key)
    rx_ticket.description()

    floatdata = 1.23456789

    sio.emit('test_response', {'message': 'Test connection from Server',
                               "hex": 0xAABBCCDDEEFF,
                               "int": 123456789,
                               "float": floatdata
                               }, room=sid)

    print("--------------------------------------------------------------")
    print(f"Test Data Send to Client [{sid}]")
    print("--------------------------------------------------------------")


@sio.on("home_setup")  # Home Data Setup
def home_setup(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Request Data Register with...")
    print(f"Data = {data}")

    # Check for existing Home Data
    check_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.HOME, {})
    db_tx_queue.put(check_tx_ticket)
    check_rx_ticket = db_connector.wait_to_return(check_tx_ticket.key)

    # If Home Data is not available, register as Received Data
    if check_rx_ticket.valid is False:
        input_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REGISTER, db_manager.DataType.HOME, data)
        db_tx_queue.put(input_tx_ticket)
        input_rx_ticket = db_connector.wait_to_return(input_tx_ticket.key)
        response_values: dict = input_rx_ticket.values[0]
    else:
        response_values: dict = check_rx_ticket.values[0]

    # Answer the results of the Home data registration
    # response_values >> home_name[str], interval_time[int], expire_count[int]
    sio.emit('home_setup_response', response_values, room=sid)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8710)), app, log_output=False)
