**English** | [简体中文](README.zh-CN.md)

This is source code from [official feetech repository](https://github.com/ftservo/FTServo_Python).

## Structure

```
root dirrectory
     |---scservo_sdk 
     |---sms_sts
     |---scscl
     |---hls
     |---imu
```
The 'scscl' 'sms_sts' 'hls' 'imu' directories contain examples of using the library.

The source code of the library is located in the `scservo_sdk` directory.

The 'scsservo_sdk' directory contains the original archive with the source code of the library from the developer.

## Usage

Tested on Linux Raspbian GNU/Linux 9.13 (stretch).
Python version Python 3.5.3

### Method 1. Clone repositry

```
$ cd /usr/src/
$ sudo git clone https://github.com/ftservo/FTServo_Python.git
$ sudo chown -R pi FTServo_Python
$ cd FTServo_Python/sms_sts
$ python3 ping.py
Succeeded to open the port
Succeeded to change the baudrate
[ID:001] ping Succeeded. SCServo model number : 1540
```

### Method 2. Install pip package

Copy the sample file to any location convenient for you. In the example I use '/home/pi/FeetechTestFiles'

```
$ pip install ftservo-python-sdk
$ cd /home/pi/FeetechTestFiles/sms_sts
$ python3 ping.py
Succeeded to open the port
Succeeded to change the baudrate
[ID:001] ping Succeeded. SCServo model number : 1540
```

## IMU Examples

### 1. Environment

```powershell
# Use the system Python (3.12.10 in this example), not the uv managed interpreter
python -m pip install pyserial
python -c "import serial, matplotlib, numpy; print('deps ok')"
```

### 2. IMU examples

| File | Purpose | Defaults |
|---|---|---|
| `imu/read_slfp.py` | Read the SLFP quaternion QX/QY/QZ (half float) and compute QW | /dev/ttyUSB0 / ID 200 / 50 Hz |
| `imu/read_gyro.py` | Read the 3-axis angular rate (raw + signed) | /dev/ttyUSB0 / ID 200 / 50 Hz |
| `imu/read_acc.py` | Read the 3-axis acceleration (raw + signed) | /dev/ttyUSB0 / ID 200 / 50 Hz |
| `imu/sync_read.py` | One sync-read packet of 15 bytes covering HLS servo + IMU | /dev/ttyUSB0 / IMU ID 200 + HLS ID 10, 11 |
| `imu/slfp_viewer.py` | 3D attitude viewer (cube + 3 axes + euler curves) | /dev/ttyUSB0 / ID 200 / 50 Hz |

> `/dev/ttyUSB0` is the Linux default; on Windows change it to `COMx`.

### 3. Run

```powershell
# console output
python imu/read_slfp.py
python imu/read_gyro.py
python imu/read_acc.py
python imu/sync_read.py

# 3D attitude viewer
python imu/slfp_viewer.py --demo             # simulated attitude, no hardware
python imu/slfp_viewer.py                    # real device, /dev/ttyUSB0 / ID 200
python imu/slfp_viewer.py --port COM7 --id 200
python imu/slfp_viewer.py --zero-on-start    # capture the attitude 1 s after start as zero
```

Typical output of `read_slfp.py` (50 lines per second; QX is the raw 16-bit value, the number in brackets is the S1E5F10 decoded float):

```
Succeeded to open the port
Succeeded to change the baudrate
[ID:200] QX:12345(0.123456) QY:... QZ:... QW:0.987654
```

### 4. 3D viewer controls

- Drag with the mouse to orbit, scroll to zoom;
- The cube follows the quaternion, the red/green/blue axes are the body X/Y/Z;
- Top right: 6 s rolling window of roll / pitch / yaw. Bottom right: quaternion, euler angles and status;
- Press `z` to use the current attitude as the new zero (click the plot area first to give the window focus);
- Closing the window stops the reader thread and releases the port; `Ctrl+C` is also handled through `finally`.
