#
# toget_home_main_station.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import subprocess
import sys
import threading


def read_subprocess_output(_process: subprocess.Popen):
    while True:
        output = _process.stdout.readline()
        if output == b'' and _process.poll() is not None:
            break
        if output:
            print(output, end='')


if __name__ == '__main__':
    print("--------------------------------------------")
    print("Start Server!!!")
    print("--------------------------------------------")

    # Subprocess Part
    subprocess_list = [
        subprocess.Popen([sys.executable, "-u",  "Connection/device_connect_manager.py"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         universal_newlines=True),
        subprocess.Popen([sys.executable, "-u", "Connection/external_connect_manager.py"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         universal_newlines=True),
        subprocess.Popen([sys.executable, "-u", "Database/json_server.py"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         universal_newlines=True)
    ]

    # Thread Part
    thread_list = []
    for process in subprocess_list:
        thread = threading.Thread(target=read_subprocess_output, args=(process,))
        thread.daemon = True
        thread.start()
        thread_list.append(thread)

    try:
        while True:
            pass  # infinite loop
    except KeyboardInterrupt:
        print("--------------------------------------------")
        print("Stopping Server!!!")
        print("--------------------------------------------")

        for process in subprocess_list:
            process.terminate()

        print("--------------------------------------------")
        print("Stopped")
        print("--------------------------------------------")
