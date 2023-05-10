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

# Active Session Part
device_session = set()


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
    print(f"Client [{sid}] Home Setup Data Register with...")
    print(f"Data = {data}")  # data >> home_name[str]

    # Check for existing Home Data
    check_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.HOME, {})
    db_tx_queue.put(check_tx_ticket)
    check_rx_ticket = db_connector.wait_to_return(check_tx_ticket.key)

    # If Home Data is not available, register as Received Data
    if check_rx_ticket.valid is False:
        input_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REGISTER, db_manager.DataType.HOME, data)
        db_tx_queue.put(input_tx_ticket)
        input_rx_ticket = db_connector.wait_to_return(input_tx_ticket.key)
        if input_rx_ticket.valid is True:  # Home Data registration successful
            recheck_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.HOME, {})
            db_tx_queue.put(recheck_tx_ticket)
            recheck_rx_ticket = db_connector.wait_to_return(recheck_tx_ticket.key)
            response_values: dict = recheck_rx_ticket.values[0]
            response_values["valid"] = recheck_rx_ticket.valid
        else:  # Home Data registration failed
            response_values: dict = input_rx_ticket.values[0]
            response_values["valid"] = input_rx_ticket.valid
    else:
        response_values: dict = check_rx_ticket.values[0]
        response_values["valid"] = check_rx_ticket.valid

    print(f"Response to Client [{sid}] Home Setup Register with...")
    print(f"Data = {response_values}")

    # Answer the results of the Home data registration
    # response_values >> home_name[str], interval_time[int], expire_count[int]
    sio.emit('home_setup_response', response_values, room=sid)
    print("--------------------------------------------------------------")


@sio.on("data_register")  # DB Data Register
def data_register(sid, data: dict):
    pass  # Todo DB Registration Function except Home and Device


@sio.on("device_register")  # Device Session & Data Register
def device_register(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Device Session & Data Register with...")
    print(f"Data = {data}")  # data >> id[option,str], familiar_name[str], user_id[str]

    device_id_option = data.get('id')

    # Check for existing Device Data
    if device_id_option is not None:
        check_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.DEVICE,
                                                {"id": device_id_option})
        db_tx_queue.put(check_tx_ticket)
        check_rx_ticket = db_connector.wait_to_return(check_tx_ticket.key)
        if check_rx_ticket.valid is True:  # Device ID exists in DB
            pass  # Todo Active Session Function Required



if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8710)), app, log_output=False)
