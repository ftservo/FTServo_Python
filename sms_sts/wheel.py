#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#
#
# Available SCServo model on this example : All models using Protocol SCS
# This example is tested with a SCServo(STS/SMS), and an URT
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
from scservo_sdk.sms_sts import sms_sts as SmsStsPacketHandler


# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler('/dev/ttyUSB0')# ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = SmsStsPacketHandler(portHandler)
    
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

scs_comm_result, scs_error = packetHandler.WheelMode(1)
if scs_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(scs_comm_result))
elif scs_error != 0:
    print("%s" % packetHandler.getRxPacketError(scs_error))

while 1:
    # Servo (ID1) accelerates to a maximum speed of V=60 * 0.732=43.92rpm at an acceleration of A=50 * 8.7deg/s ^ 2, forward rotation
    scs_comm_result, scs_error = packetHandler.WriteSpec(1, 60, 50)
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))
    if scs_error != 0:
        print("%s" % packetHandler.getRxPacketError(scs_error))

    time.sleep(5);

    # Servo (ID1) decelerates to speed 0 and stops rotating at an acceleration of A=50 * 8.7deg/s ^ 2
    scs_comm_result, scs_error = packetHandler.WriteSpec(1, 0, 50)
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))
    if scs_error != 0:
        print("%s" % packetHandler.getRxPacketError(scs_error))

    time.sleep(2);

     # Servo (ID1/ID2) accelerates to a maximum speed of V=-60 * 0.732=-43.92rpm with an acceleration of A=50 * 8.7deg/s ^ 2, reverse rotation
    scs_comm_result, scs_error = packetHandler.WriteSpec(1, -50, 50)
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))
    if scs_error != 0:
        print("%s" % packetHandler.getRxPacketError(scs_error))

    time.sleep(5);

    # Servo (ID1) decelerates to speed 0 and stops rotating at an acceleration of A=50 * 8.7deg/s ^ 2
    scs_comm_result, scs_error = packetHandler.WriteSpec(1, 0, 50)
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))
    if scs_error != 0:
        print("%s" % packetHandler.getRxPacketError(scs_error))

    time.sleep(2);
    
# Close port
portHandler.closePort()
