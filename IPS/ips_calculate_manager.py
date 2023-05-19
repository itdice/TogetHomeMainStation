#
# ips_calculate_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import sys
import os
import operator
from queue import Queue
import numpy as np  # NUMPY

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))  # Master Path Finder
from Database import db_manager


class IPSTX:
    def __init__(self, device_id: str, space_id: str, beacon_list: list):
        self.device_id = device_id
        self.space_id = space_id
        self.beacon_list = beacon_list
        self.beacon_preset_data: dict = {}


class IPSManager:
    def __init__(self, ips_queue: Queue, db_tx_queue: Queue, db_rx_queue: Queue,
                 db_connector: db_manager.DatabaseManagerSystem):
        self.ips_queue = ips_queue
        self.db_tx_queue = db_tx_queue
        self.db_rx_queue = db_rx_queue
        self.db_connector = db_connector

        self.max_trust_distance: float = 5.500
        self.max_error_distance: float = 2.223

    @staticmethod
    def rssi_converter(rssi_data: np.ndarray):
        m, n = rssi_data.shape

        if m > 1:
            print("ERROR // Data after the first row is discarded because the input data is too large.")

        converted_data = np.array([np.arange(n), rssi_data[0, :]]).T
        return converted_data

    @staticmethod
    def linear_conversion(converted_data: np.ndarray):
        m, n = converted_data.shape
        A = np.array([converted_data[:, 0], np.ones(m)]).T
        b = converted_data[:, 1]

        Q, R = np.linalg.qr(A)  # QR Decomposition
        b_hat = Q.T.dot(b)

        R_upper = R[:n, :]
        b_upper = b_hat[:n]

        slope, intercept = np.linalg.solve(R_upper, b_upper)  # Linear Solve

        return slope, intercept

    def linear_calibration(self, rssi_raw_data: np.ndarray):
        m, n = rssi_raw_data.shape
        rssi_cal_data = rssi_raw_data.copy()

        for cir in range(m):
            converted_data = self.rssi_converter(np.array([rssi_raw_data[cir, :]]))  # Convert Data
            slope, intercept = self.linear_conversion(converted_data)  # QR Decomposition and Linear Conversion

            linear_data = np.arange(n) * slope + intercept  # Create Linear Data
            all_diff = abs(rssi_raw_data[cir, :] - linear_data)  # All Difference raw <-> linear
            average_diff = all_diff.sum() / n  # Average Difference

            check_diff = all_diff - average_diff

            for num in range(n):
                if check_diff[num] > 0:  # If differance value is over average differance value, replace to linear data
                    rssi_cal_data[cir, num] = linear_data[num]

        return rssi_cal_data

    def distance(self, rssi: np.ndarray, preset: np.ndarray):
        rssi_cal_data = np.array([rssi.mean(axis=1),
                                  rssi.max(axis=1, initial=-120),
                                  rssi.min(axis=1, initial=-120)]).T

        upper_avg = preset[:, 0] - rssi_cal_data[:, 0]
        upper_max = preset[:, 0] - rssi_cal_data[:, 1]
        upper_min = preset[:, 0] - rssi_cal_data[:, 2]

        dis = 10 ** (upper_avg / (10 * 2))
        error = 10 ** (upper_min / (10 * 2)) - 10 ** (upper_max / (10 * 2))
        valid = np.ones(error.shape[0])

        for cir in range(
                error.shape[0]):  # If error value is bigger than MAX_TRUST_DISTANCE, distance value can't trust
            valid[cir] = 1 if error[cir] < self.max_trust_distance else 0

        result_data = np.array([dis, error, valid]).T

        return result_data

    def position_calculate(self, rssi: np.ndarray, pos: np.ndarray, preset: np.ndarray, trust_distance):
        dis = self.distance(rssi, preset)  # calculate distance from beacon

        A = 2 * (pos[1, 0] - pos[0, 0])
        B = 2 * (pos[1, 1] - pos[0, 1])
        C = pos[0, 0] ** 2 + pos[0, 1] ** 2 - pos[1, 0] ** 2 - pos[1, 1] ** 2 - dis[0, 0] ** 2 + dis[1, 0] ** 2
        D = 2 * (pos[2, 0] - pos[1, 0])
        E = 2 * (pos[2, 1] - pos[1, 1])
        F = pos[1, 0] ** 2 + pos[1, 1] ** 2 - pos[2, 0] ** 2 - pos[2, 1] ** 2 - dis[1, 0] ** 2 + dis[2, 0] ** 2

        result_pos = np.zeros(2)
        result_pos[0] = ((B * F) - (E * C)) / ((A * E) - (D * B))
        result_pos[1] = (-1 * (A / B)) * ((B * F) - (E * C)) / ((A * E) - (D * B)) - (C / B)

        return result_pos

    def startup(self):
        pass  # Todo Developing IPS Calculation Operations

    def space_calculate(self, beacon_list: list) -> str:  # beacon_list >> {id[str], state[str], rssi[list]}
        request_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.PRI_BEACON, {})
        self.db_tx_queue.put(request_tx_ticket)
        request_rx_ticket = self.db_connector.wait_to_return(request_tx_ticket.key)

        if request_rx_ticket.valid is False:  # Primary Beacon data does not exist
            response_value: str = "FFFFFFFFFFFF"  # Unknown Space
            return response_value

        pri_beacon_data: list = request_rx_ticket.values  # pri_beacon_data >> {beacon_id, space_id, min_rssi, max_rssi}
        space_data: dict = {}  # Space Weight Value

        for one_beacon in beacon_list:
            cur_beacon_id: str = one_beacon.get('id')
            cur_raw_beacon_rssi: list = one_beacon.get('rssi')

            cur_pac_beacon_rssi: np.ndarray = np.array([cur_raw_beacon_rssi])
            cur_fil_beacon_rssi: np.ndarray = self.linear_calibration(cur_pac_beacon_rssi)
            cur_mean_beacon_rssi: int = round(cur_fil_beacon_rssi.mean(axis=1)[0])

            for one_pri_beacon in pri_beacon_data:
                pri_beacon_id: str = one_pri_beacon.get('beacon_id')
                pri_space_id: str = one_pri_beacon.get('space_id')
                pri_min_rssi: int = one_pri_beacon.get('min_rssi')
                pri_max_rssi: int = one_pri_beacon.get('max_rssi')
                pri_mean_rssi: int = round((pri_max_rssi + pri_min_rssi) / 2)

                if space_data.get(pri_space_id) is None:  # Does not have a corresponding Space ID
                    space_data[pri_space_id] = 0

                if pri_beacon_id == cur_beacon_id:
                    if pri_min_rssi <= cur_mean_beacon_rssi <= pri_max_rssi:  # within range
                        space_data[pri_space_id] += abs(cur_mean_beacon_rssi - pri_mean_rssi)
                    else:
                        space_data[pri_space_id] += 2 * abs(cur_mean_beacon_rssi - pri_mean_rssi)

        # Output the least weighted Space ID and value
        min_weight_space = min(space_data.items(), key=operator.itemgetter(1))
        response_space_id: str = min_weight_space[0]

        return response_space_id

    def ticket_pos_request(self, tx_ticket: IPSTX) -> dict:  # Insert beacon location information into the ticket
        request_tx_ticket = db_manager.DatabaseTX(db_manager.AccessType.REQUEST, db_manager.DataType.BEACON,
                                                  {"space_id": tx_ticket.space_id})
        self.db_tx_queue.put(request_tx_ticket)
        request_rx_ticket = self.db_connector.wait_to_return(request_tx_ticket.key)

        if request_rx_ticket.valid is False:  # Failed to receive Beacon information for Space ID.
            response_values: dict = request_rx_ticket.values[0]
            response_values["valid"] = request_rx_ticket.valid
            return response_values

        beacon_preset_data: list = request_rx_ticket.values

        for one_pre_beacon in beacon_preset_data:
            cur_beacon_id: str = one_pre_beacon.get("id")
            cur_beacon_pos_x: float = one_pre_beacon.get("pos_x")
            cur_beacon_pos_y: float = one_pre_beacon.get("pos_y")
            cur_beacon_power: int = one_pre_beacon.get("power")

            cur_dic_data = {"pos_x": cur_beacon_pos_x, "pos_y": cur_beacon_pos_y, "power": cur_beacon_power}
            tx_ticket.beacon_preset_data[cur_beacon_id] = cur_dic_data

        response_values: dict = {"msg": "Successfully inserted beacon location information into ticket",
                                 "valid": True}
        return response_values
