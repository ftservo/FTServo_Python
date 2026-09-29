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
