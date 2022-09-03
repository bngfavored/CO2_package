#!/bin/bash

service dbus start
bluetoothd &
hcitool scan
bluetoothctl trust 60:C0:BF:48:38:5F
bluetoothctl pair 60:C0:BF:48:38:5F
bluetoothctl connect 60:C0:BF:48:38:5F
python ./main.py

/bin/bash