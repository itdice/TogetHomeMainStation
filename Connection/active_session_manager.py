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


class BeaconManagerSystem:
    def __init__(self, db_tx_queue: Queue, db_rx_queue: Queue, db_connector: db_manager.DatabaseManagerSystem):
        self.db_tx_queue = db_tx_queue
        self.db_rx_queue = db_rx_queue
        self.db_connector = db_connector

    def register(self, beacon_data: dict) -> dict:  # beacon_data >> id, state, space_id, pos_x, pos_y, power, isprimary
        input_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REGISTER, db_manager.DataType.BEACON,
                                                beacon_data)
        self.db_tx_queue.put(input_tx_ticket)
        input_rx_ticket = self.db_connector.wait_to_return(input_tx_ticket.key)

        response_values = input_rx_ticket.values[0]
        response_values["valid"] = input_rx_ticket.valid

        return response_values

    def update_state(self, beacon_list: list) -> bool:  # beacon_data_list >> {id[str], state[str], rssi[list]}...
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
