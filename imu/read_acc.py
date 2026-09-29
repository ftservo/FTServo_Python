#!/usr/bin/env python
#
# *********     Read ACC Example      *********
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
    # Read the current accelerometer of IMU(ID1)
    # AX/AY/AZ are the raw 16 bits value, BIT15 is the direction bit,
    # the value after "signed" is converted by scs_tohost(value, 15)
    scs_ax, scs_ay, scs_az, scs_comm_result, scs_error = packetHandler.readAcc(1)
    if scs_comm_result != COMM_SUCCESS:
        print(packetHandler.getTxRxResult(scs_comm_result))
    else:
        print("[ID:%03d] AX:%d AY:%d AZ:%d, signed AX:%d AY:%d AZ:%d" % (1,
              scs_ax, scs_ay, scs_az,
              packetHandler.scs_tohost(scs_ax, 15),
              packetHandler.scs_tohost(scs_ay, 15),
              packetHandler.scs_tohost(scs_az, 15)))
    if scs_error != 0:
        print(packetHandler.getRxPacketError(scs_error))
    time.sleep(1)

# Close port
portHandler.closePort()
