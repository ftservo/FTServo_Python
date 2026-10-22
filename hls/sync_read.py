#!/usr/bin/env python
#
# *********     Sync Read Example      *********
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
from scservo_sdk import GroupSyncRead, PortHandler, COMM_SUCCESS
from scservo_sdk.hls import hls as HlsPacketHandler
from scservo_sdk.sms_sts import SMS_STS_PRESENT_POSITION_L, SMS_STS_PRESENT_SPEED_L


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

groupSyncRead = GroupSyncRead(packetHandler, SMS_STS_PRESENT_POSITION_L, 4)

while 1:
    for scs_id in range(1, 11):
        # Add parameter storage for SCServo#1~10 present position value
        scs_addparam_result = groupSyncRead.addParam(scs_id)
        if scs_addparam_result != True:
            print("[ID:%03d] groupSyncRead addparam failed" % scs_id)

    scs_comm_result = groupSyncRead.txRxPacket()
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))

    for scs_id in range(1, 11):
        # Check if groupsyncread data of SCServo#1~10 is available
        scs_data_result, scs_error = groupSyncRead.isAvailable(scs_id, SMS_STS_PRESENT_POSITION_L, 4)
        if scs_data_result == True:
            # Get SCServo#scs_id present position value
            scs_present_position = groupSyncRead.getData(scs_id, SMS_STS_PRESENT_POSITION_L, 2)
            scs_present_speed = groupSyncRead.getData(scs_id, SMS_STS_PRESENT_SPEED_L, 2)
            print("[ID:%03d] PresPos:%d PresSpd:%d" % (scs_id, scs_present_position, packetHandler.scs_tohost(scs_present_speed, 15)))
        else:
            print("[ID:%03d] groupSyncRead getdata failed" % scs_id)
            continue
        if scs_error != 0:
            print("%s" % packetHandler.getRxPacketError(scs_error))
    groupSyncRead.clearParam()
    time.sleep(1)
# Close port
portHandler.closePort()
