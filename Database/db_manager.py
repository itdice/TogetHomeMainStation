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


class AccessType(Enum):  # Database Access Type
    REQUEST = 0x10
    REGISTER = 0x20
    UPDATE = 0x30
    DELETE = 0x40


class DataType(Enum):  # Database Data Type
    HOME = 0x10
    SPACE = 0x20
    USER = 0x30
    DEVICE = 0x40
    BEACON = 0x50
    PRI_BEACON = 0x51
    ROUTER = 0x60
    PRI_ROUTER = 0x61
    POS_DATA = 0x70


class TypeDescription:
    access = {
        AccessType.REQUEST: "Request",
        AccessType.REGISTER: "Register",
        AccessType.UPDATE: "Update",
        AccessType.DELETE: "Delete"
    }
    data = {
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


class DatabaseTX:  # Tickets containing information to send requests to the database
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
        access_name = TypeDescription.access.get(self.access_type, "Unknown")
        data_name = TypeDescription.data.get(self.data_type, "Unknown")

        print("--------------------------------------------------------------")
        print(f"Send Database Access Type = {access_name}, Data Type = {data_name}")
        print(f"Ticket Key = {self.key}")
        print(f"Contain Values =>")
        print(f"{self.values}")
        print("--------------------------------------------------------------")


class DatabaseRX:  # Tickets containing information received from the database
    def __init__(self, key: str, data_type: DataType, values: list, valid: bool):
        self.key = key
        self.data_type = data_type
        self.values = values
        self.valid = valid

    def description(self):  # Print Data
        data_name = TypeDescription.data.get(self.data_type, "Unknown")

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

    def db_request(self, tx_ticket: DatabaseTX) -> DatabaseRX:
        try:
            connection = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                         password=self.password, db=self.db, charset=self.charset)
        except pymysql.err.OperationalError as e:
            code, msg = e.args
            print(f"DB Request Connect ERROR[{code}] : {msg}")
            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, [{"msg": "Connection Fail"}], False)
            return rx_ticket

        cursor = connection.cursor()

        if tx_ticket.data_type == DataType.HOME:  # Home Data DB Response with No Option

            sql = "SELECT Home_name, Interval_time, Expire_count FROM Home"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()[0]
                response_values = [{"home_name": data[0],
                                    "interval_time": data[1],
                                    "expire_count": data[2]}]
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.SPACE:  # Space Data DB Response with No Option

            sql = "SELECT HEX(ID), Familiar_name, Size_X, Size_Y FROM Space"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()
                response_values = []
                for cube_data in data:
                    temp_data = {"id": cube_data[0],
                                 "familiar_name": cube_data[1],
                                 "size_x": cube_data[2],
                                 "size_y": cube_data[3]}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.USER:  # User Data DB Response with No Option

            sql = "SELECT HEX(ID), User_name FROM User"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()
                response_values = []
                for cube_data in data:
                    temp_data = {"id": cube_data[0],
                                 "user_name": cube_data[1]}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.DEVICE:  # Device Data DB Response with UserID Option
            user_id_option = tx_ticket.values.get("user_id")

            sql = "SELECT HEX(ID), Familiar_name, HEX(State), HEX(UserID) FROM Device"
            if user_id_option is not None:
                sql = sql + f"WHERE HEX(UserID) = '{user_id_option}'"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()
                response_values = []
                for cube_data in data:
                    temp_data = {"id": cube_data[0],
                                 "familiar_name": cube_data[1],
                                 "state": cube_data[2],
                                 "user_id": cube_data[3]}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.BEACON:  # Beacon Data DB Response with SpaceID and isPrimary Option
            space_id_option = tx_ticket.values.get("space_id")
            isprimary_option = tx_ticket.values.get("isprimary")

            sql = "SELECT HEX(ID), HEX(State), HEX(SpaceID), Pos_X, Pos_Y, Power, isPrimary FROM Beacon"
            if space_id_option is None and isprimary_option is not None:
                sql = sql + f"WHERE isPrimary = {isprimary_option}"
            elif space_id_option is not None and isprimary_option is None:
                sql = sql + f"WHERE HEX(SpaceID) = '{space_id_option}'"
            else:
                sql = sql + f"WHERE HEX(SpaceID) = '{space_id_option}' AND isPrimary = {isprimary_option}"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()
                response_values = []
                for cube_data in data:
                    temp_data = {"id": cube_data[0],
                                 "state": cube_data[1],
                                 "space_id": cube_data[2],
                                 "pos_x": cube_data[3],
                                 "pos_y": cube_data[4],
                                 "power": cube_data[5],
                                 "isprimary": cube_data[6]}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.PRI_BEACON:  # Primary Beacon RSSI Data Response with No Option

            sql = "SELECT HEX(BeaconID), HEX(SpaceID), Min_RSSI, Max_RSSI FROM PRI_Beacon"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()
                response_values = []
                for cube_data in data:
                    temp_data = {"beacon_id": cube_data[0],
                                 "space_id": cube_data[1],
                                 "min_rssi": cube_data[2],
                                 "max_rssi": cube_data[3]}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.ROUTER:  # Router Data Response with No Option

            sql = "SELECT HEX(ID), SSID, MAC FROM Router"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()
                response_values = []
                for cube_data in data:
                    temp_data = {"id": cube_data[0],
                                 "ssid": cube_data[1],
                                 "mac": cube_data[2]}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.PRI_ROUTER:  # Primary Router RSSI Data Response with No Option

            sql = "SELECT HEX(RouterID), HEX(SpaceID), Min_RSSI, Max_RSSI FROM PRI_Router"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()
                response_values = []
                for cube_data in data:
                    temp_data = {"router_id": cube_data[0],
                                 "space_id": cube_data[1],
                                 "min_rssi": cube_data[2],
                                 "max_rssi": cube_data[3]}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.POS_DATA:  # Position Data Response with No Option

            sql = "SELECT HEX(DeviceID), HEX(SpaceID), Pos_X, Pos_Y FROM Pos_Data"

            count = cursor.execute(sql)
            if count > 0:
                response_valid = True
                data = cursor.fetchall()
                response_values = []
                for cube_data in data:
                    temp_data = {"device_id": cube_data[0],
                                 "space_id": cube_data[1],
                                 "pos_x": cube_data[2],
                                 "pos_y": cube_data[3]}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        else:  # Type Error
            print(f"DB Request Type Error")
            response_valid = False
            response_values = [{"msg": "Data Type Error"}]

        rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, response_values, response_valid)
        return rx_ticket

    def db_register(self, tx_ticket: DatabaseTX) -> DatabaseRX:
        pass

    def db_update(self, tx_ticket: DatabaseTX) -> DatabaseRX:
        pass

    def db_delete(self, tx_ticket: DatabaseTX) -> DatabaseRX:
        pass

    def update_id_list(self):
        try:
            connection = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                         password=self.password, db=self.db, charset=self.charset)
        except pymysql.err.OperationalError as e:
            code, msg = e.args
            print(f"Update ID List Func Connect ERROR[{code}] : {msg}")
            return None

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
