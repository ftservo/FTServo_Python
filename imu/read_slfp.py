#!/usr/bin/env python
#
# *********     Read SLFP(Quaternion) Example      *********
#
#
# Available SCServo model on this example : All models using Protocol SCS(IMU)
# This example is tested with a IMU, and an URT
#

import sys
import time

sys.path.append("..")
from scservo_sdk import *                      # Uses FTServo SDK library


# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler('/dev/ttyUSB0')# ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = imu(portHandler)

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
    # Read the current quaternion of IMU(ID1)
    # QX/QY/QZ are the raw 16 bits value(half float), the value in bracket is decoded by S1E5F10,
    # QW is calculated by sqrt(1 - QX^2 - QY^2 - QZ^2), QW is 0 when QX^2 + QY^2 + QZ^2 > 1
    scs_qx, scs_qy, scs_qz, scs_qw, scs_comm_result, scs_error = packetHandler.readSlfp(1)
    if scs_comm_result != COMM_SUCCESS:
        print(packetHandler.getTxRxResult(scs_comm_result))
    else:
        print("[ID:%03d] QX:%d(%f) QY:%d(%f) QZ:%d(%f) QW:%f" % (1,
              scs_qx, packetHandler.scs_halffloat(scs_qx),
              scs_qy, packetHandler.scs_halffloat(scs_qy),
              scs_qz, packetHandler.scs_halffloat(scs_qz), scs_qw))
    if scs_error != 0:
        print(packetHandler.getRxPacketError(scs_error))
    time.sleep(1)

# Close port
portHandler.closePort()
