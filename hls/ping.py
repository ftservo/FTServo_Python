#!/usr/bin/env python
#
# *********     Ping Example      *********
#
#
# Available SCServo model on this example : All models using Protocol SCS
# This example is tested with a SCServo(HLS), and an URT
#

import sys
import os
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
portHandler = PortHandler('/dev/ttyUSB0') #ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

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

# Try to ping the ID:1 FTServo
# Get SCServo model number
scs_model_number, scs_comm_result, scs_error = packetHandler.ping(1)
if scs_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(scs_comm_result))
else:
    print("[ID:%03d] ping Succeeded. SCServo model number : %d" % (1, scs_model_number))
if scs_error != 0:
    print("%s" % packetHandler.getRxPacketError(scs_error))

# Close port
portHandler.closePort()
