#
# position_export_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import pymysql


class PositionManagerSystem:
    def __init__(self):
        self.host = 'localhost'
        self.port = 3306
        self.user = 'jsonmanager'
        self.password = '17fd1cefff705e7f803e'
        self.db = 'togethome'
        self.charset = 'utf8'

    def get(self) -> dict:
        try:
            connection = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                         password=self.password, db=self.db, charset=self.charset)
        except pymysql.err.OperationalError as e:
            code, msg = e.args
            print(f"Position Manager Connect ERROR[{code}] : {msg}")
            json_data = {"msg": "Connection Failed"}
            return json_data

        cursor = connection.cursor()
        key_list: list = ['device_id', 'device_name', 'device_state', 'space_id', 'space_name',
                          'space_size_x', 'space_size_y', 'pos_x', 'pos_y', 'data_time']
        result_json_data: dict = {"device_data": []}

        sql = f"""
        SELECT HEX(DeviceID),
        (SELECT Familiar_name FROM Device WHERE Device.ID = Pos_Data.DeviceID) AS Device_Name,
        (SELECT HEX(State) FROM Device WHERE Device.ID = Pos_Data.DeviceID) AS Device_State,
        HEX(SpaceID),
        (SELECT Familiar_name FROM Space WHERE Space.ID = Pos_Data.SpaceID) AS Space_name,
        (SELECT Size_X FROM Space WHERE Space.ID = Pos_Data.SpaceID) AS Space_Size_X,
        (SELECT Size_Y FROM Space WHERE Space.ID = Pos_Data.SpaceID) AS Space_Size_Y,
        Pos_X, Pos_Y,
        DATE_FORMAT(Data_time, '%Y-%m-%d %H:%i:%s') AS Date_time
        FROM Pos_Data
        """

        count = cursor.execute(sql)
        if count > 0:
            result_json_data["valid"] = True
            result_json_data["device_count"] = 0
            total_data = cursor.fetchall()
            for data in total_data:
                result_json_data["device_count"] += 1
                result_json_data["device_data"].append(dict(zip(key_list, data)))
        else:
            result_json_data["valid"] = False
            result_json_data["device_count"] = 0
            result_json_data["msg"] = "No Position Data"

        connection.commit()
        connection.close()

        return result_json_data
