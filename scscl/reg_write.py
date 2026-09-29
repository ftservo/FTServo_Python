#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#
#
# Available SCServo model on this example : All models using Protocol SCS
# This example is tested with a SCServo(SCS), and an URT
#

import sys
import os
import time

sys.path.append("..")
from scservo_sdk import *                      # Uses FTServo SDK library


# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler('/dev/ttyUSB0')# ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = scscl(portHandler)
    
# Open port
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    quit()

# Set port baudrate 1000000
if portHandler.setBaudRate(1000000):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    quit()

while 1:
    # Servo (ID1~10) runs at a maximum speed ofV=1500*0.059=88.5rpm until it reaches position P1=1000
    for scs_id in range(1, 11):
        scs_comm_result, scs_error = packetHandler.RegWritePos(scs_id, 1000, 0, 1500)
        if scs_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(scs_comm_result))
        if scs_error != 0:
            print("%s" % packetHandler.getRxPacketError(scs_error))
    packetHandler.RegAction()

    time.sleep((1000-20)/(1500) + 0.1)#//[(P1-P0)/(V)] + 0.1

    # Servo (ID1~10) runs at a maximum speed ofV=1500*0.059=88.5rpm until it reaches position P0=20
    for scs_id in range(1, 11):
        scs_comm_result, scs_error = packetHandler.RegWritePos(scs_id, 20, 0, 1500)
        if scs_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(scs_comm_result))
        if scs_error != 0:
            print("%s" % packetHandler.getRxPacketError(scs_error))
    packetHandler.RegAction()

    time.sleep((1000-20)/(1500) + 0.1)#//[(P1-P0)/(V)] + 0.1

# Close port
portHandler.closePort()
