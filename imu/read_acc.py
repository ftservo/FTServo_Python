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

    # Read the current accelerometer of IMU(ID200)
    # AX/AY/AZ are the raw 16 bits value, BIT15 is the direction bit,
    # the value after "signed" is converted by scs_tohost(value, 15)
    scs_ax, scs_ay, scs_az, scs_comm_result, scs_error = packetHandler.readAcc(IMU_ID)
    if scs_comm_result != COMM_SUCCESS:
        print(packetHandler.getTxRxResult(scs_comm_result))
    else:
        print("[ID:%03d] AX:%d AY:%d AZ:%d, signed AX:%d AY:%d AZ:%d" % (IMU_ID,
              scs_ax, scs_ay, scs_az,
              packetHandler.scs_tohost(scs_ax, 15),
              packetHandler.scs_tohost(scs_ay, 15),
              packetHandler.scs_tohost(scs_az, 15)))
    if scs_error != 0:
        print(packetHandler.getRxPacketError(scs_error))
    # Keep the sampling period 20ms(50Hz)
    delay = SAMPLE_PERIOD - (time.time() - start_time)
    time.sleep(delay if delay > 0 else 0)

# Close port
portHandler.closePort()
