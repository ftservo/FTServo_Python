#!/usr/bin/env python

import math as _math

from .scservo_def import *
from .protocol_packet_handler import *
from .group_sync_read import *
from .group_sync_write import *

#内存表定义
#-------EPROM(只读)--------
IMU_MODEL_L = 3
IMU_MODEL_H = 4

#-------EPROM(读写)--------
IMU_ID = 5
IMU_BAUD_RATE = 6
IMU_GYRO_DPS = 11
IMU_ACC_SCAL = 12
IMU_SFLP_ODR = 13

#-------SRAM(读写)--------
IMU_LOCK = 55

#-------SRAM(只读)--------
IMU_PRESENT_SLFP_QXL = 56
IMU_PRESENT_SLFP_QXH = 57
IMU_PRESENT_SLFP_QYL = 58
IMU_PRESENT_SLFP_QYH = 59
IMU_PRESENT_SLFP_QZL = 60
IMU_PRESENT_SLFP_QZH = 61
IMU_PRESENT_GYRO_WXL = 62
IMU_PRESENT_GYRO_WXH = 63
IMU_PRESENT_GYRO_WYL = 65
IMU_PRESENT_GYRO_WYH = 66
IMU_PRESENT_GYRO_WZL = 68
IMU_PRESENT_GYRO_WZH = 69
IMU_PRESENT_ACC_AXL = 71
IMU_PRESENT_ACC_AXH = 72
IMU_PRESENT_ACC_AYL = 74
IMU_PRESENT_ACC_AYH = 75
IMU_PRESENT_ACC_AZL = 77
IMU_PRESENT_ACC_AZH = 78

class imu(protocol_packet_handler):
    def __init__(self, portHandler):
        protocol_packet_handler.__init__(self, portHandler, 0)
        self.groupSyncWrite = GroupSyncWrite(self, 0, 0)

    def readSlfpQxyz(self, scs_id):
        data, result, error = self.readTxRx(scs_id, IMU_PRESENT_SLFP_QXL, 6)
        if result != COMM_SUCCESS:
            return 0, 0, 0, result, error
        if len(data) < 6:
            return 0, 0, 0, COMM_RX_CORRUPT, error
        qx = self.scs_makeword(data[0], data[1])
        qy = self.scs_makeword(data[2], data[3])
        qz = self.scs_makeword(data[4], data[5])
        return qx, qy, qz, result, error

    def scs_slfp_qw(self, qx, qy, qz):
        #由四元数QX/QY/QZ原始16位值计算QW = sqrt(1 - QX^2 - QY^2 - QZ^2)
        #内存表说明：QX^2+QY^2+QZ^2 > 1 时先归一化或直接把QW置0，此处按QW置0处理
        fx = self.scs_halffloat(qx)
        fy = self.scs_halffloat(qy)
        fz = self.scs_halffloat(qz)
        value = 1.0 - fx * fx - fy * fy - fz * fz
        return _math.sqrt(value) if (value > 0.0) else 0.0

    def readSlfp(self, scs_id):
        qx, qy, qz, result, error = self.readSlfpQxyz(scs_id)
        qw = self.scs_slfp_qw(qx, qy, qz) if (result == COMM_SUCCESS) else 0.0
        return qx, qy, qz, qw, result, error

    def readGyro(self, scs_id):
        length = IMU_PRESENT_GYRO_WZH - IMU_PRESENT_GYRO_WXL + 1
        data, result, error = self.readTxRx(scs_id, IMU_PRESENT_GYRO_WXL, length)
        if result != COMM_SUCCESS:
            return 0, 0, 0, result, error
        if len(data) < length:
            return 0, 0, 0, COMM_RX_CORRUPT, error
        offset_y = IMU_PRESENT_GYRO_WYL - IMU_PRESENT_GYRO_WXL
        offset_z = IMU_PRESENT_GYRO_WZL - IMU_PRESENT_GYRO_WXL
        wx = self.scs_makeword(data[0], data[1])
        wy = self.scs_makeword(data[offset_y], data[offset_y + 1])
        wz = self.scs_makeword(data[offset_z], data[offset_z + 1])
        return wx, wy, wz, result, error

    def readAcc(self, scs_id):
        length = IMU_PRESENT_ACC_AZH - IMU_PRESENT_ACC_AXL + 1
        data, result, error = self.readTxRx(scs_id, IMU_PRESENT_ACC_AXL, length)
        if result != COMM_SUCCESS:
            return 0, 0, 0, result, error
        if len(data) < length:
            return 0, 0, 0, COMM_RX_CORRUPT, error
        offset_y = IMU_PRESENT_ACC_AYL - IMU_PRESENT_ACC_AXL
        offset_z = IMU_PRESENT_ACC_AZL - IMU_PRESENT_ACC_AXL
        ax = self.scs_makeword(data[0], data[1])
        ay = self.scs_makeword(data[offset_y], data[offset_y + 1])
        az = self.scs_makeword(data[offset_z], data[offset_z + 1])
        return ax, ay, az, result, error

    def LockEprom(self, scs_id):
        return self.write1ByteTxRx(scs_id, IMU_LOCK, 1)

    def unLockEprom(self, scs_id):
        return self.write1ByteTxRx(scs_id, IMU_LOCK, 0)
