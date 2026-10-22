#!/usr/bin/env python
#
# *********     Sync Write Example      *********
#
#
# Available SCServo model on this example : All models using Protocol SCS
# This example is tested with a SCServo(HLS), and an URT
#

import sys
import os
import time
from pathlib import Path

# Make the project root(which contains scservo_sdk/) importable,
# independent of the current working directory
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import only the symbols used in this example
from scservo_sdk import PortHandler, COMM_SUCCESS
from scservo_sdk.hls import hls as HlsPacketHandler


# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler('/dev/ttyUSB0')# ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = HlsPacketHandler(portHandler)
    
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
    for scs_id in range(1, 11):
        # Add servo(id)#1~10 goal position\moving speed\moving accc value to the Syncwrite parameter storage
        # Servo (ID1~10) runs at a maximum speed of V=60 * 0.732=43.92rpm and an acceleration of A=50 * 8.7deg/s ^ 2 until it reaches position P1=4095
         # torque=500
        scs_addparam_result = packetHandler.SyncWritePosEx(scs_id, 4095, 60, 50, 500)
        if scs_addparam_result != True:
            print("[ID:%03d] groupSyncWrite addparam failed" % scs_id)

    # Syncwrite goal position
    scs_comm_result = packetHandler.groupSyncWrite.txPacket()
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))

    # Clear syncwrite parameter storage
    packetHandler.groupSyncWrite.clearParam()

    time.sleep(((4095-0)/(60*50) + (60*50)/(50*100) + 0.05))#[(P1-P0)/(V*50)] + [(V*50)/(A*100)] + 0.05

    for scs_id in range(1, 11):
        # Add servo#1~10 goal position\moving speed\moving accc value to the Syncwrite parameter storage
        # Servo (ID1~10) runs at a maximum speed of V=60 * 0.732=43.92rpm and an acceleration of A=50 * 8.7deg/s ^ 2 until P0=0 position
        # torque=500
        scs_addparam_result = packetHandler.SyncWritePosEx(scs_id, 0, 60, 50, 500)
        if scs_addparam_result != True:
            print("[ID:%03d] groupSyncWrite addparam failed" % scs_id)

    # Syncwrite goal position
    scs_comm_result = packetHandler.groupSyncWrite.txPacket()
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))
    
    # Clear syncwrite parameter storage
    packetHandler.groupSyncWrite.clearParam()
    
    time.sleep(((4095-0)/(60*50) + (60*50)/(50*100) + 0.05))#[(P1-P0)/(V*50)] + [(V*50)/(A*100)] + 0.05

# Close port
portHandler.closePort()
