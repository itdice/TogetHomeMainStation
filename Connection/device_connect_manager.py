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
from Connection import active_session_manager
from IPS import ips_calculate_manager

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
active_connector = active_session_manager.StateManagerSystem(db_tx_queue, db_rx_queue, db_connector)

# IPS Part
ips_queue = Queue(maxsize=4096)
ips_connector = ips_calculate_manager.IPSManager(ips_queue, db_tx_queue, db_rx_queue, db_connector)
ips_thread = threading.Thread(target=ips_connector.startup, args=())
ips_thread.daemon = True
ips_thread.start()


@sio.event
def connect(sid, environ):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Connected!!!")
    print("--------------------------------------------------------------")


@sio.event
def disconnect(sid):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Disconnected!!!")
    response_values: dict = active_connector.device_disconnect(sid)
    print(f"Result of Client [{sid}] Device Disconnected with...")
    print(f"Data = {response_values}")
    print("--------------------------------------------------------------")


@sio.on("test_send")
def test_send(sid, data):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] send Data")
    print(f"Data = {data}")
    print("--------------------------------------------------------------")


@sio.on("test_request")
def test_request(sid):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] request Test Data!!!")
    print("--------------------------------------------------------------")

    """
    table_list = [db_manager.DataType.HOME, db_manager.DataType.USER, db_manager.DataType.SPACE,
                  db_manager.DataType.BEACON, db_manager.DataType.DEVICE]

    for cir in table_list:
        tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, cir, {})
        db_tx_queue.put(tx_ticket)
        rx_ticket = db_connector.wait_to_return(tx_ticket.key)
        rx_ticket.description()
    """

    sio.emit('test_response', [{'message': 'Test connection from Server',
                                "hex": 0xAABBCCDDEEFF,
                                "int": 123456789,
                                "float": 1.2345678
                               }], room=sid)

    print("--------------------------------------------------------------")
    print(f"Test Data Send to Client [{sid}]")
    print("--------------------------------------------------------------")


@sio.on("data_request")  # DB Data Request
def data_request(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Data Request with...")
    print(f"Data = {data}")  # data >> data_type[str], `id[str], `user_id[str], `space_id[str], `isprimary[bool]

    data_type_str = data.get("data_type")
    data_type: db_manager.DataType = db_manager.TypeDescription.re_data.get(data_type_str)

    request_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, data_type, data)
    db_tx_queue.put(request_tx_ticket)
    request_rx_ticket = db_connector.wait_to_return(request_tx_ticket.key)

    response_list: list = request_rx_ticket.values
    response_list[0]["valid"] = request_rx_ticket.valid
    print(f"Response to Client [{sid}] Request Data with...")
    print(f"Data = {response_list}")

    # Answer the results of DB Requests
    # response_values >> Answers in list form, different result values for each data type
    sio.emit('data_request_response', response_list, room=sid)
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


@sio.on("device_register")  # Device Session & Data Register
def device_register(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Device Session & Data Register with...")
    print(f"Data = {data}")  # data >> `id[str], familiar_name[str], user_id[str]

    device_id_option = data.get('id')

    # Check for existing Device Data
    if device_id_option is not None:
        check_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.DEVICE,
                                                {"id": device_id_option})
        db_tx_queue.put(check_tx_ticket)
        check_rx_ticket = db_connector.wait_to_return(check_tx_ticket.key)
        if check_rx_ticket.valid is True:  # Device ID exists in DB
            response_values: dict = active_connector.device_connect(sid, device_id_option)
            print(f"Response to Client [{sid}] Device Register with...")
            print(f"Data = {response_values}")

            # Answer the results of the Device data registration
            # response_values >> msg[str], valid[bool]
            sio.emit('device_register_response', response_values, room=sid)
            print("--------------------------------------------------------------")
            return None

    # Device ID does not exist in DB or Device ID has not been received
    input_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REGISTER, db_manager.DataType.DEVICE, data)
    db_tx_queue.put(input_tx_ticket)
    input_rx_ticket = db_connector.wait_to_return(input_tx_ticket.key)

    input_response_values: dict = input_rx_ticket.values[0]
    input_response_values["valid"] = input_rx_ticket.valid
    registered_id = input_response_values.get("id")

    if registered_id is not None:  # If the reply message has a newly registered ID
        response_values: dict = active_connector.device_connect(sid, registered_id)
        print(f"Response to Client [{sid}] Device Register with...")
        print(f"Data = {response_values}")

        # Answer the results of the Device data registration
        # response_values >> msg[str], valid[bool]
        sio.emit('device_register_response', response_values, room=sid)
        print("--------------------------------------------------------------")
        return None
    else:  # Device registration failed
        print(f"Response to Client [{sid}] Device Register with...")
        print(f"Data = {input_response_values}")

        # Answer the results of the Device data registration
        # response_values >> msg[str], valid[bool]
        sio.emit('device_register_response', input_response_values, room=sid)
        print("--------------------------------------------------------------")
        return None


@sio.on("data_register")  # DB Data Register excluding Home and Device
def data_register(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Data Register with...")
    print(f"Data = {data}")  # data >> data_type[str], `(Different datas for each data type)

    data_type_str = data.get("data_type")
    data_type: db_manager.DataType = db_manager.TypeDescription.re_data.get(data_type_str)

    request_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REGISTER, data_type, data)
    db_tx_queue.put(request_tx_ticket)
    request_rx_ticket = db_connector.wait_to_return(request_tx_ticket.key)

    response_list: list = request_rx_ticket.values
    response_list[0]["valid"] = request_rx_ticket.valid
    print(f"Response to Client [{sid}] Register Data with...")
    print(f"Data = {response_list}")

    # Answer the results of DB Register
    # response_values >> Answers in list form, different result values for each data type
    sio.emit('data_register_response', response_list, room=sid)
    print("--------------------------------------------------------------")


@sio.on("data_update")  # DB Data Update
def data_update(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Data Update with...")
    print(f"Data = {data}")  # data >> data_type[str], `(Different datas for each data type)

    data_type_str = data.get("data_type")
    data_type: db_manager.DataType = db_manager.TypeDescription.re_data.get(data_type_str)

    request_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.UPDATE, data_type, data)
    db_tx_queue.put(request_tx_ticket)
    request_rx_ticket = db_connector.wait_to_return(request_tx_ticket.key)

    response_list: list = request_rx_ticket.values
    response_list[0]["valid"] = request_rx_ticket.valid
    print(f"Response to Client [{sid}] Update Data with...")
    print(f"Data = {response_list}")

    # Answer the results of DB Update
    # response_values >> Answers in list form, different result values for each data type
    sio.emit('data_update_response', response_list, room=sid)
    print("--------------------------------------------------------------")


@sio.on("data_delete")  # DB Data Delete
def data_delete(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] Data Delete with...")
    print(f"Data = {data}")  # data >> data_type[str], `(Different datas for each data type)

    data_type_str = data.get("data_type")
    data_type: db_manager.DataType = db_manager.TypeDescription.re_data.get(data_type_str)

    request_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.DELETE, data_type, data)
    db_tx_queue.put(request_tx_ticket)
    request_rx_ticket = db_connector.wait_to_return(request_tx_ticket.key)

    response_list: list = request_rx_ticket.values
    response_list[0]["valid"] = request_rx_ticket.valid
    print(f"Response to Client [{sid}] Delete Data with...")
    print(f"Data = {response_list}")

    # Answer the results of DB Delete
    # response_values >> Answers in list form, different result values for each data type
    sio.emit('data_delete_response', response_list, room=sid)
    print("--------------------------------------------------------------")


@sio.on("ips_space")  # IPS Space Calculate Request
def ips_space(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] IPS Space Calculate with...")
    print(f"Data = {data}")  # data >> beacon_rssi_data[list]

    # Device State Update Part
    device_state_update: dict = active_connector.device_update(sid, active_session_manager.StateType.PROCESSING)
    print(f"Client [{sid}] Device State Update Response ...")
    print(f"Data = {device_state_update}")

    beacon_rssi_data: list = data.get("beacon_rssi_data")

    # Beacon State Update Part
    if active_connector.beacon_state_update(beacon_rssi_data) is True:
        print(f"Client [{sid}] --> Successfully updated beacon status information.")
    else:
        print(f"Client [{sid}] --> Failed to update beacon status information.")

    result_space_id: str = ips_connector.space_calculate(beacon_rssi_data)  # IPS Space Calculate

    if result_space_id == "FFFFFFFFFFFF":  # Space calculation failed
        response_values: dict = {"msg": "Space calculation failed", "valid": False,
                                 "space_id": result_space_id}
        # Device State Update Part
        device_state_update: dict = active_connector.device_update(sid, active_session_manager.StateType.MISSING)
        print(f"Client [{sid}] Device State Update Response ...")
        print(f"Data = {device_state_update}")
    else:  # Space calculation successful
        # Space Size Part
        space_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.SPACE,
                                                {"id": result_space_id})
        db_tx_queue.put(space_tx_ticket)
        space_rx_ticket = db_connector.wait_to_return(space_tx_ticket.key)

        if space_rx_ticket.valid is True:  # If Space Data exists
            space_size_x: float = space_rx_ticket.values[0].get("size_x")
            space_size_y: float = space_rx_ticket.values[0].get("size_y")

            # Change the position to the center of the space.
            device_id = active_connector.session_info.get(sid)
            space_position_values: dict = {"device_id": device_id, "space_id": result_space_id,
                                           "pos_x": space_size_x / 2, "pos_y": space_size_y / 2}
            ips_connector.position_update(space_position_values)

        response_values: dict = {"msg": "Space calculation successful", "valid": True,
                                 "space_id": result_space_id}

    print(f"Response to Client [{sid}] IPS Space Calculate with...")
    print(f"Data = {response_values}")

    # Answer the results of the IPS Space Calculate
    # response_values >> msg[str], valid[bool], space_id[str]
    sio.emit('ips_space_response', response_values, room=sid)
    print("--------------------------------------------------------------")


@sio.on("ips_final")  # IPS Final Calculate Request
def ips_final(sid, data: dict):
    print("--------------------------------------------------------------")
    print(f"Client [{sid}] IPS Space Calculate with...")
    print(f"Data = {data}")  # data >> device_id[str], space_id[str], beacon_rssi_data[list]

    device_id: str = data.get("device_id")
    space_id: str = data.get("space_id")
    beacon_rssi_data: list = data.get("beacon_rssi_data")

    # Beacon State Update Part
    if active_connector.beacon_state_update(beacon_rssi_data) is True:
        print(f"Client [{sid}] --> Successfully updated beacon status information.")
    else:
        print(f"Client [{sid}] --> Failed to update beacon status information.")

    # IPS Ticket and Beacon Position Update Part
    ips_ticket = ips_calculate_manager.IPSTX(device_id, space_id, beacon_rssi_data)
    ticket_pos_response: dict = ips_connector.ticket_pos_request(ips_ticket)

    if ticket_pos_response.get("valid") is True:
        print(f"DeviceID : [{device_id}]'s IPS Ticket Beacon Position Update Success.")
        ips_queue.put(ips_ticket)
        # Device State Update Part
        device_state_update: dict = active_connector.device_update(sid, active_session_manager.StateType.NORMAL)
    else:
        print(f"DeviceID : [{device_id}]'s IPS Ticket Beacon Position Update Failed.")
        # Device State Update Part
        device_state_update: dict = active_connector.device_update(sid, active_session_manager.StateType.MISSING)

    print(f"Client [{sid}] Device State Update Response ...")
    print(f"Data = {device_state_update}")
    print("--------------------------------------------------------------")


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8710)), app, log_output=False)
