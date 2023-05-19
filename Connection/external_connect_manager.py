#
# external_connect_manager.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import socket
import time


def broadcast_message(msg: str, port: int, term: int):
    print("--------------------------------------------")
    print("External Broadcast Message Service is START!!")
    print("--------------------------------------------")

    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Socket
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Set Socket Options

    try:
        while True:
            soc.sendto(msg.encode(), ('<broadcast>', port))  # Send broadcast msg
            time.sleep(term)  # Wait for the specified time
    except KeyboardInterrupt:
        print("--------------------------------------------")
        print("External Broadcast Message Service is STOP!!")
        print("--------------------------------------------")
        soc.close()  # Socket Close


if __name__ == '__main__':
    message: str = "Toget_Home_Main_Station_Server_17fd1cefff705e7f803e"
    port_number: int = 8711
    term_time: int = 1

    broadcast_message(message, port_number, term_time)
