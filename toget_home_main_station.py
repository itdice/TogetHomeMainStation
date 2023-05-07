#
# toget_home_main_station.py
# Toget Home Main Station Server
#
# Created by IT DICE on 2023/04/30.
#
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))  # Master Path Finder
from Connection import device_connect_manager
from Connection import external_connect_manager
from Database import position_export_manager