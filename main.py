#
# main.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/17.
#
import uvicorn
import socketio

sio = socketio.AsyncServer()
app = socketio.ASGIApp(sio)


@sio.event
async def connect(sid, environ, auth):
    print(f'connected auth = {auth} sid = {sid}')
    await sio.emit('hello', {'message': 'Hello',
                             "hex": 0xAABBCCDDEEFF,
                             "int": 123456789,
                             "double": 1.23456789
                             }, to=sid)


@sio.event
def disconnect(sid):
    print(f"disconnected sid = {sid}")


@sio.on("test")
def test_event(sid, data):
    print(f"Test sid = {sid} data = {data}")


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8710)
