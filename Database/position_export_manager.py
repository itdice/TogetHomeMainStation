#
# position_export_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import flask
import flask_socketio

app = flask.Flask(__name__)
app.secret_key = '17fd1cefff705e7f803e'
sio = flask_socketio.SocketIO(app)

@app.route("/position.json")
def position_json():
