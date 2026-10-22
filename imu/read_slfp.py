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
from pathlib import Path

# Make the project root(which contains scservo_sdk/) importable,
# independent of the current working directory
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import only the symbols used in this example
from scservo_sdk import PortHandler, COMM_SUCCESS
from scservo_sdk.imu import imu as ImuPacketHandler


# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler('/dev/ttyUSB0')# ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = ImuPacketHandler(portHandler)

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

# IMU ID on the bus
IMU_ID = 200

# Sampling period: 20ms -> 50Hz
SAMPLE_PERIOD = 0.02

while 1:
    start_time = time.time()

    # Read the current quaternion of IMU(ID200)
    # QX/QY/QZ are the raw 16 bits value(half float), the value in bracket is decoded by S1E5F10,
    # QW is calculated by sqrt(1 - QX^2 - QY^2 - QZ^2), QW is 0 when QX^2 + QY^2 + QZ^2 > 1
    scs_qx, scs_qy, scs_qz, scs_qw, scs_comm_result, scs_error = packetHandler.readSlfp(IMU_ID)
    if scs_comm_result != COMM_SUCCESS:
        print(packetHandler.getTxRxResult(scs_comm_result))
    else:
        print("[ID:%03d] QX:%d(%f) QY:%d(%f) QZ:%d(%f) QW:%f" % (IMU_ID,
              scs_qx, packetHandler.scs_halffloat(scs_qx),
              scs_qy, packetHandler.scs_halffloat(scs_qy),
              scs_qz, packetHandler.scs_halffloat(scs_qz), scs_qw))
    if scs_error != 0:
        print(packetHandler.getRxPacketError(scs_error))
    # Keep the sampling period 20ms(50Hz)
    delay = SAMPLE_PERIOD - (time.time() - start_time)
    time.sleep(delay if delay > 0 else 0)

# Close port
portHandler.closePort()
