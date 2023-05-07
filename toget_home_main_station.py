#
# toget_home_main_station.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import socketio
import eventlet
from enum import Enum
from queue import Queue

sio = socketio.Server(async_mode="eventlet")
app = socketio.WSGIApp(sio)