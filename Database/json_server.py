#
# position_export_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/05/08.
#
import json
import flask
import flask_socketio
import position_export_manager

app = flask.Flask(__name__)
app.secret_key = '17fd1cefff705e7f803e'
sio = flask_socketio.SocketIO(app)
position_connector = position_export_manager.PositionManagerSystem()


@app.route("/position.json")
def position_json():
    str_data = position_connector.get()  # Request Position Data
    json_data = json.dumps(str_data, ensure_ascii=False, indent=4)
    web_data = flask.make_response(json_data)
    return web_data


if __name__ == '__main__':
    sio.run(app, host='0.0.0.0', port=8712, debug=True)
