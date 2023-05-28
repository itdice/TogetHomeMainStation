#
# db_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import time
import string
import random
import pymysql
from enum import Enum
from queue import Queue
from threading import Lock


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
    re_data = {
        "Home": DataType.HOME,
        "Space": DataType.SPACE,
        "User": DataType.USER,
        "Device": DataType.DEVICE,
        "Beacon": DataType.BEACON,
        "Primary Beacon": DataType.PRI_BEACON,
        "Router": DataType.ROUTER,
        "Primary Router": DataType.PRI_ROUTER,
        "Position Data": DataType.POS_DATA
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
        self.tx_queue: Queue = tx_queue
        self.rx_queue: Queue = rx_queue
        self.id_list: list = []
        self.rx_key_list: list = []
        self.lock = Lock()

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
            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, [{"msg": "Connection Failed"}], False)
            return rx_ticket

        cursor = connection.cursor()

        if tx_ticket.data_type == DataType.HOME:  # Home Data DB Request with No Option
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
        elif tx_ticket.data_type == DataType.SPACE:  # Space Data DB Request with SpaceID Option
            space_id_option = tx_ticket.values.get("id")

            sql = "SELECT HEX(ID), Familiar_name, Size_X, Size_Y FROM Space"
            if space_id_option is not None:
                sql += f"WHERE HEX(ID) = '{space_id_option}'"

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
        elif tx_ticket.data_type == DataType.USER:  # User Data DB Request with No Option
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
        elif tx_ticket.data_type == DataType.DEVICE:  # Device Data DB Request with DeviceID and UserID Option
            device_id_option = tx_ticket.values.get("id")
            user_id_option = tx_ticket.values.get("user_id")

            sql = "SELECT HEX(ID), Familiar_name, HEX(State), HEX(UserID) FROM Device"
            if device_id_option is not None and user_id_option is None:
                sql += f" WHERE HEX(ID) = '{device_id_option}'"
            elif device_id_option is None and user_id_option is not None:
                sql += f" WHERE HEX(UserID) = '{user_id_option}'"
            elif device_id_option is not None and user_id_option is not None:
                sql += f" WHERE HEX(ID) = '{device_id_option}' AND HEX(UserID) = '{user_id_option}'"
            else:
                sql += f""

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
        elif tx_ticket.data_type == DataType.BEACON:  # Beacon Data DB Request with SpaceID and isPrimary Option
            space_id_option = tx_ticket.values.get("space_id")
            isprimary_option = tx_ticket.values.get("isprimary")

            sql = "SELECT HEX(ID), HEX(State), HEX(SpaceID), Pos_X, Pos_Y, Power, isPrimary FROM Beacon"
            if space_id_option is None and isprimary_option is not None:
                sql += f" WHERE isPrimary = {bool(isprimary_option)}"
            elif space_id_option is not None and isprimary_option is None:
                sql += f" WHERE HEX(SpaceID) = '{space_id_option}'"
            elif space_id_option is not None and isprimary_option is not None:
                sql += f" WHERE HEX(SpaceID) = '{space_id_option}' AND isPrimary = {bool(isprimary_option)}"
            else:
                sql += f""

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
                                 "isprimary": bool(cube_data[6])}
                    response_values.append(temp_data)
            else:
                response_valid = False
                response_values = [{"msg": "No Data"}]
        elif tx_ticket.data_type == DataType.PRI_BEACON:  # Primary Beacon RSSI Data Request with No Option
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
        elif tx_ticket.data_type == DataType.ROUTER:  # Router Data Request with No Option
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
        elif tx_ticket.data_type == DataType.PRI_ROUTER:  # Primary Router RSSI Data Request with No Option
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
        elif tx_ticket.data_type == DataType.POS_DATA:  # Position Data Request with DeviceID Option
            device_id_option = tx_ticket.values.get("device_id")

            sql = "SELECT HEX(DeviceID), HEX(SpaceID), Pos_X, Pos_Y FROM Pos_Data"
            if device_id_option is not None:
                sql += f"WHERE HEX(DeviceID) = '{device_id_option}'"

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
            print(f"DB Request Data Type Error")
            response_valid = False
            response_values = [{"msg": "Data Type Error"}]

            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, response_values, response_valid)
            return rx_ticket

        connection.commit()
        connection.close()

        rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, response_values, response_valid)
        return rx_ticket

    def db_register(self, tx_ticket: DatabaseTX) -> DatabaseRX:
        self.update_id_list()  # Update the ID List to generate a new ID
        try:
            connection = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                         password=self.password, db=self.db, charset=self.charset)
        except pymysql.err.OperationalError as e:
            code, msg = e.args
            print(f"DB Register Connect ERROR[{code}] : {msg}")
            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, [{"msg": "Connection Failed"}], False)
            return rx_ticket

        cursor = connection.cursor()

        if tx_ticket.data_type == DataType.HOME:  # Home Data DB Register
            registered_id = "FFFFFFFFFFFF"

            sql = f"""
            INSERT INTO Home(Home_name, Interval_time, Expire_count)
            VALUES ('{tx_ticket.values.get('home_name', 'Empty')}',
            {tx_ticket.values.get('interval_time', 60)}, {tx_ticket.values.get('expire_count', 5)})"""
        elif tx_ticket.data_type == DataType.SPACE:  # Space Data DB Register
            registered_id = self.new_id(DataType.SPACE)

            sql = f"""
            INSERT INTO Space(ID, Familiar_name, Size_X, Size_Y)
            VALUES (UNHEX('{registered_id}'), '{tx_ticket.values.get('familiar_name')}',
            {tx_ticket.values.get('size_x', 0.0)}, {tx_ticket.values.get('size_y', 0.0)})"""
        elif tx_ticket.data_type == DataType.USER:  # User Data DB Register
            registered_id = self.new_id(DataType.USER)

            sql = f"""
            INSERT INTO User(ID, User_name)
            VALUES (UNHEX('{registered_id}'),
            '{tx_ticket.values.get('user_name')}')"""
        elif tx_ticket.data_type == DataType.DEVICE:  # Device Data DB Register
            registered_id = self.new_id(DataType.DEVICE)

            sql = f"""
            INSERT INTO Device(ID, Familiar_name, State, UserID)
            VALUES (UNHEX('{registered_id}'), '{tx_ticket.values.get('familiar_name')}',
            UNHEX('{tx_ticket.values.get('state', 'FFFF')}'),
            UNHEX('{tx_ticket.values.get('user_id')}'))"""
        elif tx_ticket.data_type == DataType.BEACON:  # Beacon Data DB Register
            registered_id = "FFFFFFFFFFFF"

            sql = f"""
            INSERT INTO Beacon(ID, State, SpaceID, Pos_X, Pos_Y, Power, isPrimary)
            VALUES (UNHEX('{tx_ticket.values.get('id')}'),
            UNHEX('{tx_ticket.values.get('state', 'FFFF')}'),
            UNHEX('{tx_ticket.values.get('space_id')}'),
            {tx_ticket.values.get('pos_x', 0.0)},
            {tx_ticket.values.get('pos_y', 0.0)},
            {tx_ticket.values.get('power', -62)},
            {bool(tx_ticket.values.get('isprimary', 0))})"""
        elif tx_ticket.data_type == DataType.PRI_BEACON:  # Primary Beacon RSSI Data DB Register
            registered_id = "FFFFFFFFFFFF"

            sql = f"""
            INSERT INTO PRI_Beacon(BeaconID, SpaceID, Min_RSSI, Max_RSSI)
            VALUES (UNHEX('{tx_ticket.values.get('beacon_id')}'),
            UNHEX('{tx_ticket.values.get('space_id')}'),
            {tx_ticket.values.get('min_rssi', -70)},
            {tx_ticket.values.get('max_rssi', -50)})"""
        elif tx_ticket.data_type == DataType.ROUTER:  # Router Data DB Register
            registered_id = self.new_id(DataType.ROUTER)

            sql = f"""
            INSERT INTO Router(ID, SSID, MAC)
            VALUES (UNHEX('{registered_id}'), '{tx_ticket.values.get('ssid')}',
            UNHEX('{tx_ticket.values.get('mac')}'))"""
        elif tx_ticket.data_type == DataType.PRI_ROUTER:  # Primary Router RSSI Data DB Register
            registered_id = "FFFFFFFFFFFF"

            sql = f"""
            INSERT INTO PRI_Router(RouterID, SpaceID, Min_RSSI, Max_RSSI)
            VALUES (UNHEX('{tx_ticket.values.get('router_id')}'),
            UNHEX('{tx_ticket.values.get('space_id')}'),
            {tx_ticket.values.get('min_rssi', -90)},
            {tx_ticket.values.get('max_rssi', -70)})"""
        elif tx_ticket.data_type == DataType.POS_DATA:  # Position Data DB Register
            registered_id = "FFFFFFFFFFFF"

            sql = f"""
            INSERT INTO Pos_Data(DeviceID, SpaceID, Pos_X, Pos_Y)
            VALUES (UNHEX('{tx_ticket.values.get('device_id')}'),
            UNHEX('{tx_ticket.values.get('space_id')}'),
            {tx_ticket.values.get('pos_x', 0.0)},
            {tx_ticket.values.get('pos_y', 0.0)})"""
        else:  # Type Error
            print(f"DB Register Data Type Error")
            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type,
                                   [{"msg": "Data Type Error"}], False)
            return rx_ticket

        count = cursor.execute(sql)
        if count == 1:
            response_valid = True
            response_values = [{"msg": "Register Success", "id": registered_id}]
        else:
            response_valid = False
            response_values = [{"msg": "Register Failed"}]

        connection.commit()
        connection.close()

        rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, response_values, response_valid)
        return rx_ticket

    def db_update(self, tx_ticket: DatabaseTX) -> DatabaseRX:
        try:
            connection = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                         password=self.password, db=self.db, charset=self.charset)
        except pymysql.err.OperationalError as e:
            code, msg = e.args
            print(f"DB Update Connect ERROR[{code}] : {msg}")
            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, [{"msg": "Connection Fail"}], False)
            return rx_ticket

        cursor = connection.cursor()

        if tx_ticket.data_type == DataType.HOME:  # Home Setting Data Update
            sql = f"""
            UPDATE Home
            SET Interval_time = {tx_ticket.values.get('interval_time')},
            Expire_count = {tx_ticket.values.get('expire_count')}
            WHERE Home_name = '{tx_ticket.values.get('home_name')}'
            """
        elif tx_ticket.data_type == DataType.SPACE:  # Space Size Update
            sql = f"""
            UPDATE Space
            SET Size_X = {tx_ticket.values.get('size_x')},
            Size_Y = {tx_ticket.values.get('size_y')}
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.USER:  # User Name Update
            sql = f"""
            UPDATE User
            SET User_name = '{tx_ticket.values.get('user_name')}'
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.DEVICE:  # Device State Update
            sql = f"""
            UPDATE Device
            SET State = UNHEX('{tx_ticket.values.get('state')}')
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.BEACON:  # Beacon State or Power Update
            if tx_ticket.values.get('state') is not None and tx_ticket.values.get('isprimary') is None \
                    and tx_ticket.values.get('power') is None:
                sql = f"""
                UPDATE Beacon
                SET State = UNHEX('{tx_ticket.values.get('state')}')
                WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
                """
            elif tx_ticket.values.get('state') is None and tx_ticket.values.get('isprimary') is not None \
                    and tx_ticket.values.get('power') is None:
                sql = f"""
                UPDATE Beacon
                SET isPrimary = {bool(tx_ticket.values.get('isprimary'))}
                WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
                """
            elif tx_ticket.values.get('state') is None and tx_ticket.values.get('isprimary') is None \
                    and tx_ticket.values.get('power') is not None:
                sql = f"""
                UPDATE Beacon
                SET Power = {tx_ticket.values.get('power')}
                WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
                """
            else:
                print(f"DB Beacon Update Value Error")
                rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type,
                                       [{"msg": "Beacon Update Value Error"}], False)
                return rx_ticket
        elif tx_ticket.data_type == DataType.PRI_BEACON:  # Primary Beacon RSSI Value Update
            sql = f"""
            UPDATE PRI_Beacon
            SET Min_RSSI = {tx_ticket.values.get('min_rssi')},
            Max_RSSI = {tx_ticket.values.get('max_rssi')}
            WHERE HEX(BeaconID) = '{tx_ticket.values.get('beacon_id')}' AND
            HEX(SpaceID) = '{tx_ticket.values.get('space_id')}'
            """
        elif tx_ticket.data_type == DataType.ROUTER:  # Router SSID Update
            sql = f"""
            UPDATE Router
            SET SSID = '{tx_ticket.values.get('ssid')}'
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.PRI_ROUTER:  # Primary Router RSSI Value Update
            sql = f"""
            UPDATE PRI_Router
            SET Min_RSSI = {tx_ticket.values.get('min_rssi')},
            Max_RSSI = {tx_ticket.values.get('max_rssi')}
            WHERE HEX(RouterID) = '{tx_ticket.values.get('router_id')}' AND
            HEX(SpaceID) = '{tx_ticket.values.get('space_id')}'
            """
        elif tx_ticket.data_type == DataType.POS_DATA:  # Position Data Update
            sql = f"""
            UPDATE Pos_Data
            SET SpaceID = UNHEX('{tx_ticket.values.get('space_id')}'),
            Pos_X = {tx_ticket.values.get('pos_x')},
            Pos_Y = {tx_ticket.values.get('pos_y')}
            WHERE HEX(DeviceID) = '{tx_ticket.values.get('device_id')}'
            """
        else:  # Type Error
            print(f"DB Update Data Type Error")
            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type,
                                   [{"msg": "Data Type Error"}], False)
            return rx_ticket

        count = cursor.execute(sql)
        if count == 1:
            response_valid = True
            response_values = [{"msg": "Update Success"}]
        else:
            response_valid = False
            response_values = [{"msg": "Update Failed"}]

        connection.commit()
        connection.close()

        rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, response_values, response_valid)
        return rx_ticket

    def db_delete(self, tx_ticket: DatabaseTX) -> DatabaseRX:
        try:
            connection = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                         password=self.password, db=self.db, charset=self.charset)
        except pymysql.err.OperationalError as e:
            code, msg = e.args
            print(f"DB Delete Connect ERROR[{code}] : {msg}")
            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, [{"msg": "Connection Fail"}], False)
            return rx_ticket

        cursor = connection.cursor()

        if tx_ticket.data_type == DataType.HOME:  # Home Data Delete
            sql = f"""
            DELETE FROM Home
            WHERE Home_name = '{tx_ticket.values.get('home_name')}'
            """
        elif tx_ticket.data_type == DataType.SPACE:  # Space Data Delete
            sql = f"""
            DELETE FROM Space
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.USER:  # User Data Delete
            sql = f"""
            DELETE FROM User
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.DEVICE:  # Device Data Delete
            sql = f"""
            DELETE FROM Device
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.BEACON:  # Beacon Data Delete
            sql = f"""
            DELETE FROM Beacon
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.PRI_BEACON:  # Primary Beacon RSSI Data Delete
            sql = f"""
            DELETE FROM PRI_Beacon
            WHERE HEX(SpaceID) = '{tx_ticket.values.get('space_id')}'
            """
        elif tx_ticket.data_type == DataType.ROUTER:  # Router Data Delete
            sql = f"""
            DELETE FROM Router
            WHERE HEX(ID) = '{tx_ticket.values.get('id')}'
            """
        elif tx_ticket.data_type == DataType.PRI_ROUTER:  # Primary Router RSSI Data Delete
            sql = f"""
            DELETE FROM PRI_Router
            WHERE HEX(SpaceID) = '{tx_ticket.values.get('space_id')}'
            """
        elif tx_ticket.data_type == DataType.POS_DATA:  # Position Data Delete
            sql = f"""
            DELETE FROM Pos_Data
            WHERE HEX(DeviceID) = '{tx_ticket.values.get('device_id')}' and
            HEX(SpaceID) = '{tx_ticket.values.get('space_id')}'
            """
        else:  # Type Error
            print(f"DB Delete Data Type Error")
            rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type,
                                   [{"msg": "Data Type Error"}], False)
            return rx_ticket

        count = cursor.execute(sql)
        if count >= 0:
            response_valid = True
            response_values = [{"msg": "Delete Success"}]
        else:
            response_valid = False
            response_values = [{"msg": "Delete Failed"}]

        connection.commit()
        connection.close()

        rx_ticket = DatabaseRX(tx_ticket.key, tx_ticket.data_type, response_values, response_valid)
        return rx_ticket

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

    def startup(self):
        while True:
            now_task: DatabaseTX = self.tx_queue.get(block=True, timeout=None)

            if now_task.access_type == AccessType.REQUEST:
                return_ticket = self.db_request(now_task)
            elif now_task.access_type == AccessType.REGISTER:
                return_ticket = self.db_register(now_task)
            elif now_task.access_type == AccessType.UPDATE:
                return_ticket = self.db_update(now_task)
            elif now_task.access_type == AccessType.DELETE:
                return_ticket = self.db_delete(now_task)
            else:
                return_ticket = DatabaseRX(now_task.key, now_task.data_type, [{"msg": "Access Error"}], False)

            self.rx_queue.put(return_ticket)
            self.rx_key_list.append(return_ticket.key)

    def wait_to_return(self, ticket_key: str) -> DatabaseRX:
        while True:
            if len(self.rx_key_list) > 0:
                with self.lock:
                    if self.rx_key_list[0] == ticket_key:
                        data_task: DatabaseRX = self.rx_queue.get()
                        self.rx_key_list.pop(0)
                        return data_task
                    time.sleep(0.01)
