#!/usr/bin/env python
#
# *********     Sync Read Example      *********
#
#
# Available SCServo model on this example : HLS servo and IMU on the same bus
# This example is tested with a SCServo(HLS), a IMU and an URT
#
# Read 15 bytes from address 56(HLS_PRESENT_POSITION_L == IMU_PRESENT_SLFP_QXL) by sync read(0x82) in one packet:
#   HLS servo : 56-57 position, 58-59 speed, 60-61 load, 62 voltage, 63 temperature,
#               66 moving, 69-70 current
#   IMU       : 56-57 QX, 58-59 QY, 60-61 QZ, 62-63 WX, 64 undefined, 65-66 WY,
#               67 undefined, 68-69 WZ, 70 undefined
#

import sys
import time

sys.path.append("..")
from scservo_sdk import *                       # Uses SCServo SDK library


# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler('COM5')# ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

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

# Sync read ID range: ID_START ~ IMU_ID-1 are HLS servos, IMU_ID(the last ID) is the IMU
# In this example: ID1 is a HLS servo, ID2 is the IMU, please change them to the ID on your bus
ID_START = 1
ID_NUM = 3
IMU_ID = ID_START + ID_NUM - 1

# Sync read start address: HLS_PRESENT_POSITION_L(56) == IMU_PRESENT_SLFP_QXL(56), 15 bytes in total
SYNC_READ_ADDR = HLS_PRESENT_POSITION_L
SYNC_READ_LEN = 15

# Sampling period: 20ms -> 50Hz
SAMPLE_PERIOD = 0.02

groupSyncRead = GroupSyncRead(packetHandler, SYNC_READ_ADDR, SYNC_READ_LEN)

while 1:
    start_time = time.time()

    # Separator to make each sampling output clear
    print("--------------------------------------------------")

    for scs_id in range(ID_START, IMU_ID + 1):
        # Add parameter storage for SCServo#scs_id present status value
        scs_addparam_result = groupSyncRead.addParam(scs_id)
        if scs_addparam_result != True:
            print("[ID:%03d] groupSyncRead addparam failed" % scs_id)

    scs_comm_result = groupSyncRead.txRxPacket()
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))

    for scs_id in range(ID_START, IMU_ID + 1):
        # Check if groupsyncread data of SCServo#scs_id is available
        scs_data_result, scs_error = groupSyncRead.isAvailable(scs_id, SYNC_READ_ADDR, SYNC_READ_LEN)
        if scs_data_result != True:
            print("[ID:%03d] groupSyncRead getdata failed" % scs_id)
            continue

        if scs_id == IMU_ID:
            # ---------- the last ID is the IMU: output quaternion and gyroscope ----------
            # Get the 15 bytes data from address IMU_PRESENT_SLFP_QXL
            data = []
            for addr in range(SYNC_READ_ADDR, SYNC_READ_ADDR + SYNC_READ_LEN):
                data.append(groupSyncRead.getData(scs_id, addr, 1))
            print("[ID:%03d] SyncRead[%d~%d]:%s" % (scs_id, IMU_PRESENT_SLFP_QXL, IMU_PRESENT_SLFP_QXL + SYNC_READ_LEN - 1,
                                                    " ".join(["%02X" % value for value in data])))

            # 56-57 QX, 58-59 QY, 60-61 QZ: half float(S1E5F10), QW = sqrt(1 - QX^2 - QY^2 - QZ^2)
            scs_qx = groupSyncRead.getData(scs_id, IMU_PRESENT_SLFP_QXL, 2)
            scs_qy = groupSyncRead.getData(scs_id, IMU_PRESENT_SLFP_QYL, 2)
            scs_qz = groupSyncRead.getData(scs_id, IMU_PRESENT_SLFP_QZL, 2)
            scs_qw = packetHandler.scs_slfp_qw(scs_qx, scs_qy, scs_qz)
            print("[ID:%03d] QX:%d(%f) QY:%d(%f) QZ:%d(%f) QW:%f" % (scs_id,
                  scs_qx, packetHandler.scs_halffloat(scs_qx),
                  scs_qy, packetHandler.scs_halffloat(scs_qy),
                  scs_qz, packetHandler.scs_halffloat(scs_qz), scs_qw))

            # 62-63 WX, 65-66 WY, 68-69 WZ: raw 16 bits value, BIT15 is the direction bit,
            # the value after "signed" is converted by scs_tohost(value, 15)
            scs_wx = groupSyncRead.getData(scs_id, IMU_PRESENT_GYRO_WXL, 2)
            scs_wy = groupSyncRead.getData(scs_id, IMU_PRESENT_GYRO_WYL, 2)
            scs_wz = groupSyncRead.getData(scs_id, IMU_PRESENT_GYRO_WZL, 2)
            print("[ID:%03d] WX:%d WY:%d WZ:%d, signed WX:%d WY:%d WZ:%d" % (scs_id, scs_wx, scs_wy, scs_wz,
                  packetHandler.scs_tohost(scs_wx, 15),
                  packetHandler.scs_tohost(scs_wy, 15),
                  packetHandler.scs_tohost(scs_wz, 15)))

            # 64, 67, 70 are undefined bytes
            print("[ID:%03d] Register[64]:0x%02X Register[67]:0x%02X Register[70]:0x%02X are undefined bytes" % (scs_id,
                  data[64 - IMU_PRESENT_SLFP_QXL], data[67 - IMU_PRESENT_SLFP_QXL], data[70 - IMU_PRESENT_SLFP_QXL]))
        else:
            # ---------- other IDs are HLS servos: output present status per HLS memory table ----------
            # 56-57 position(signed 15 bits, 0~4095), 58-59 speed(signed 15 bits, rpm = V*0.732),
            # 60-61 load(signed 15 bits, 0.1%), 62 voltage(0.1V), 63 temperature(1C),
            # 66 moving(0:stopped 1:moving), 69-70 current(signed 15 bits, 6.5mA)
            scs_present_position = groupSyncRead.getData(scs_id, HLS_PRESENT_POSITION_L, 2)
            scs_present_speed = groupSyncRead.getData(scs_id, HLS_PRESENT_SPEED_L, 2)
            scs_present_load = groupSyncRead.getData(scs_id, HLS_PRESENT_LOAD_L, 2)
            scs_present_voltage = groupSyncRead.getData(scs_id, HLS_PRESENT_VOLTAGE, 1)
            scs_present_temperature = groupSyncRead.getData(scs_id, HLS_PRESENT_TEMPERATURE, 1)
            scs_present_current = groupSyncRead.getData(scs_id, HLS_PRESENT_CURRENT_L, 2)
            scs_moving = groupSyncRead.getData(scs_id, HLS_MOVING, 1)
            print("[ID:%03d] PresPos:%d PresSpd:%d PresLoad:%d PresVolt:%.1fV PresTemp:%d PresCur:%d Moving:%d" % (
                  scs_id,
                  packetHandler.scs_tohost(scs_present_position, 15),
                  packetHandler.scs_tohost(scs_present_speed, 15),
                  packetHandler.scs_tohost(scs_present_load, 15),
                  scs_present_voltage / 10.0,
                  scs_present_temperature,
                  packetHandler.scs_tohost(scs_present_current, 15),
                  scs_moving))

        if scs_error != 0:
            print("%s" % packetHandler.getRxPacketError(scs_error))

    groupSyncRead.clearParam()

    # Keep the sampling period 20ms(50Hz)
    delay = SAMPLE_PERIOD - (time.time() - start_time)
    time.sleep(delay if delay > 0 else 0)

# Close port
portHandler.closePort()
