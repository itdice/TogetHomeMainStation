#
# db_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import string
import random
import pymysql
from enum import Enum
from queue import Queue


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
    def __init__(self, access_type: AccessType, data_type: DataType, values: dict):
        self.key = self.key_generator()
        self.access_type = access_type
        self.data_type = data_type
        self.values = values

    @staticmethod
    def key_generator() -> str:  # Database TX Ticket key
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
    def __init__(self, key: str, data_type: DataType, values: dict, valid: bool):
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


class DatabaseManagerSystem:
    def __init__(self, tx_queue: Queue, rx_queue: Queue):
        self.tx_queue = tx_queue
        self.rx_queue = rx_queue
        self.id_list = []

        self.host = 'localhost'
        self.port = 3306
        self.user = 'mainstation'
        self.password = '17fd1cefff705e7f803e'
        self.db = 'togethome'
        self.charset = 'utf8'

    def update_id_list(self):
        connection = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                     password=self.password, db=self.db, charset=self.charset)
        cursor = connection.cursor()
        sql_list = ["User", "Space", "Router", "Device", "Beacon"]

        for type_name in sql_list:
            sql = "SELECT ID FROM " + type_name
            cursor.execute(sql)
            result = cursor.fetchall()
            for data in result:
                self.id_list.append(data[0].hex().upper())

        connection.commit()
        connection.close()

    def new_id(self, data_type: DataType) -> str:
        start_num = {DataType.USER: 0x100000000000,
                     DataType.SPACE: 0x200000000000,
                     DataType.ROUTER: 0x400000000000,
                     DataType.DEVICE: 0x600000000000
                     }
        end_num = {DataType.USER: 0x1FFFFFFFFFFF,
                   DataType.SPACE: 0x3FFFFFFFFFFF,
                   DataType.ROUTER: 0x5FFFFFFFFFFF,
                   DataType.DEVICE: 0x9FFFFFFFFFFF
                   }

        granted = False  # Unique check
        result = ""

        while not granted:  # Generates a unique hex ID
            int_result = random.randrange(start_num[data_type], end_num[data_type])
            str_result = hex(int_result).upper()[2:]
            if str_result in self.id_list:
                granted = False
            else:
                granted = True
                result = str_result

        return result
