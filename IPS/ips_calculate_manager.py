#
# ips_calculate_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
from queue import Queue
import numpy as np  # NUMPY


class IPSTX:
    def __init__(self):
        pass  # Todo Create IPS Ticket


class IPSManager:
    def __init__(self, ips_queue: Queue, db_tx_queue: Queue, db_rx_queue: Queue):
        self.ips_queue = ips_queue
        self.db_tx_queue = db_tx_queue
        self.db_rx_queue = db_rx_queue

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
