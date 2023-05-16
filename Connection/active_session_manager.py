#
# active_session_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/05/16.
#
import sys
import os
from enum import Enum
from queue import Queue

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))  # Master Path Finder
from Database import db_manager


class StateType(Enum):  # Device, Beacon State Type
    NORMAL = 0x00  # Device, Beacon
    TRIGGERED = 0x10  # Beacon
    LOW_BATTERY = 0x20  # Beacon
    CHARGE = 0x30  # Beacon
    PROCESSING = 0x40  # Device
    MISSING = 0x50  # Device
    DISCONNECTED = 0x60  # Device, Beacon
    INITIAL = 0xFF  # Device, Beacon


class StateDescription:
    letter = {
        StateType.NORMAL: "Normal",
        StateType.TRIGGERED: "Triggered",
        StateType.LOW_BATTERY: "Low Battery",
        StateType.CHARGE: "Charge",
        StateType.PROCESSING: "Processing",
        StateType.MISSING: "Missing",
        StateType.DISCONNECTED: "Disconnected",
        StateType.INITIAL: "Initial State"
    }
    number = {
        StateType.NORMAL: "00",
        StateType.TRIGGERED: "10",
        StateType.LOW_BATTERY: "20",
        StateType.CHARGE: "30",
        StateType.PROCESSING: "40",
        StateType.MISSING: "50",
        StateType.DISCONNECTED: "60",
        StateType.INITIAL: "FF"
    }


class StateManagerSystem:
    def __init__(self, db_tx_queue: Queue, db_rx_queue: Queue, db_connector: db_manager.DatabaseManagerSystem):
        self.db_tx_queue = db_tx_queue
        self.db_rx_queue = db_rx_queue
        self.db_connector = db_connector

        self.active_device_id: set = set()
        self.session_info: dict = {}

    def beacon_state_update(self, beacon_list: list) -> bool:  # beacon_data_list >> {id[str], state[str], rssi[list]}
        result_list: list = []

        for one_beacon in beacon_list:
            beacon_id: str = one_beacon.get('id')
            beacon_state: str = one_beacon.get('state')

            update_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.UPDATE, db_manager.DataType.BEACON,
                                                     {"id": beacon_id, "state": beacon_state})
            self.db_tx_queue.put(update_tx_ticket)
            update_rx_ticket = self.db_connector.wait_to_return(update_tx_ticket.key)
            result_list.append(update_rx_ticket.valid)

        if False in result_list:  # If any of the rx tickets return False
            conclusion = False
        else:  # If all rx tickets return True
            conclusion = True

        return conclusion

    def device_connect(self, session_id, device_id: str) -> dict:
        self.active_device_id.add(device_id)
        self.session_info[session_id] = device_id

        update_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.UPDATE, db_manager.DataType.DEVICE,
                                                 {"id": device_id,
                                                  "state": StateDescription.number.get(StateType.NORMAL) + "00"})
        self.db_tx_queue.put(update_tx_ticket)
        update_rx_ticket = self.db_connector.wait_to_return(update_tx_ticket.key)

        response_values: dict = update_rx_ticket.values[0]
        response_values["valid"] = update_rx_ticket.valid
        return response_values

    def device_update(self, session_id, state: StateType) -> dict:
        device_id = self.session_info.get(session_id)
        if device_id is not None:  # Verify Active Device
            update_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.UPDATE, db_manager.DataType.DEVICE,
                                                     {"id": device_id,
                                                      "state": StateDescription.number.get(state) + "00"})
            self.db_tx_queue.put(update_tx_ticket)
            update_rx_ticket = self.db_connector.wait_to_return(update_tx_ticket.key)

            response_values: dict = update_rx_ticket.values[0]
            response_values["valid"] = update_rx_ticket.valid
            return response_values
        else:
            response_values: dict = {"msg": "This device is not Active", "valid": False}
            return response_values

    def device_disconnect(self, session_id) -> dict:
        device_id = self.session_info.get(session_id)
        if device_id is not None:  # Verify Active Device
            self.active_device_id.remove(device_id)
            del (self.session_info[session_id])

            data: dict = {"id": device_id, "state": StateDescription.number.get(StateType.DISCONNECTED) + "00"}
            update_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.UPDATE, db_manager.DataType.DEVICE, data)
            self.db_tx_queue.put(update_tx_ticket)
            update_rx_ticket = self.db_connector.wait_to_return(update_tx_ticket.key)

            response_values: dict = update_rx_ticket.values[0]
            response_values["valid"] = update_rx_ticket.valid
            return response_values
        else:
            response_values: dict = {"msg": "This device is not Active", "valid": False}
            return response_values
