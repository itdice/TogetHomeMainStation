#
# db_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import string
from enum import Enum
import random


class AccessType(Enum):
    REQUEST = 0x10
    REGISTER = 0x20
    UPDATE = 0x30
    DELETE = 0x40


access_description = {
    AccessType.REQUEST: "Request",
    AccessType.REGISTER: "Register",
    AccessType.UPDATE: "Update",
    AccessType.DELETE: "Delete"
}


class DataType(Enum):
    HOME = 0x10
    SPACE = 0x20
    USER = 0x30
    DEVICE = 0x40
    BEACON = 0x50
    PRI_BEACON = 0x51
    ROUTER = 0x60
    PRI_ROUTER = 0x61
    POS_DATA = 0x70


type_description = {
    DataType.HOME: "Home",
    DataType.SPACE: "Space",
    DataType.USER: "User",
    DataType.DEVICE: "Device",
    DataType.BEACON: "Beacon",
    DataType.PRI_BEACON: "Primary Beacon",
    DataType.ROUTER: "Router",
    DataType.PRI_ROUTER: "Primary Router",
    DataType.POS_DATA: "Position Data"
}


class DatabaseTX:
    def __init__(self, access_type, data_type, values):
        self.key = self.key_generator()
        self.access_type = access_type
        self.data_type = data_type
        self.values = values

    @staticmethod
    def key_generator():  # Database TX Ticket key
        length = 32
        string_pool = string.ascii_letters + string.digits

        key = ""
        for cir in range(length):
            key += random.choice(string_pool)

        return key

    def description(self):  # Print Data
        access_name = access_description.get(self.access_type, "Unknown")
        data_name = type_description.get(self.data_type, "Unknown")

        print("--------------------------------------------------------------")
        print(f"Send Database Access Type = {access_name}, Data Type = {data_name}")
        print(f"Ticket Key = {self.key}")
        print(f"Contain Values =>")
        print(f"{self.values}")
        print("--------------------------------------------------------------")


class DatabaseRX:
    def __init__(self, key, data_type, values, valid):
        self.key = key
        self.data_type = data_type
        self.values = values
        self.valid = valid

    def description(self):  # Print Data
        data_name = type_description.get(self.data_type, "Unknown")

        print("--------------------------------------------------------------")
        print(f"Receive Database Data Type = {data_name}")
        print(f"Ticket Key = {self.key}")
        print(f"Contain Values =>")
        print(f"{self.values}")
        print("--------------------------------------------------------------")
