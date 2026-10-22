[English](README.md) | **简体中文**

本仓库代码来自 [feetech 官方仓库](https://github.com/ftservo/FTServo_Python)。

## 目录结构

```
根目录
     |---scservo_sdk 
     |---sms_sts
     |---scscl
     |---hls
     |---imu
```

`scscl`、`sms_sts`、`hls`、`imu` 四个目录是使用该库的示例。

库的源码位于 `scservo_sdk` 目录。

`scservo_sdk` 目录包含开发者提供的原版库源码压缩内容。

## 用法

原版示例在 Linux Raspbian GNU/Linux 9.13 (stretch)、Python 3.5.3 下测试通过。

### 方式 1：克隆仓库

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

### 方式 2：安装 pip 包

把示例文件复制到任意方便的位置，下面以 `/home/pi/FeetechTestFiles` 为例：

```
$ pip install ftservo-python-sdk
$ cd /home/pi/FeetechTestFiles/sms_sts
$ python3 ping.py
Succeeded to open the port
Succeeded to change the baudrate
[ID:001] ping Succeeded. SCServo model number : 1540
```

## IMU 运行实例说明

### 1. 环境准备

```powershell
# 使用系统 Python（本例 3.12.10），不要使用 uv 托管的解释器
python -m pip install pyserial
python -c "import serial, matplotlib, numpy; print('deps ok')"
```

### 2. IMU 示例一览

| 文件 | 功能 | 默认参数 |
|---|---|---|
| `imu/read_slfp.py` | 读 SLFP 四元数 QX/QY/QZ（半精度），反算 QW | /dev/ttyUSB0 / ID 200 / 50 Hz |
| `imu/read_gyro.py` | 读三轴角速度（原始值 + 有符号值） | /dev/ttyUSB0 / ID 200 / 50 Hz |
| `imu/read_acc.py` | 读三轴加速度（原始值 + 有符号值） | /dev/ttyUSB0 / ID 200 / 50 Hz |
| `imu/sync_read.py` | 一次同步读 HLS 舵机 + IMU 的 15 字节 | /dev/ttyUSB0 / IMU ID 200 + HLS ID 10、11 |
| `imu/slfp_viewer.py` | 四元数 3D 姿态可视化（立方体 + 三轴 + 欧拉角曲线） | /dev/ttyUSB0 / ID 200 / 50 Hz |

> 表中 `/dev/ttyUSB0` 为 Linux 默认值，Windows 上需改成 `COMx`。

### 3. 运行示例

```powershell
# 控制台打印
python imu/read_slfp.py
python imu/read_gyro.py
python imu/read_acc.py
python imu/sync_read.py

# 3D 姿态可视化
python imu/slfp_viewer.py --demo             # 无硬件，模拟姿态（先验证渲染链路）
python imu/slfp_viewer.py                    # 真实设备，默认 /dev/ttyUSB0 / ID 200
python imu/slfp_viewer.py --port COM7 --id 200
python imu/slfp_viewer.py --zero-on-start    # 启动 1 秒后把当前姿态设为 0
```

`read_slfp.py` 典型输出（每秒 50 行，QX 为原始 16 位值，括号内为 S1E5F10 解码后的浮点）：

```
Succeeded to open the port
Succeeded to change the baudrate
[ID:200] QX:12345(0.123456) QY:... QZ:... QW:0.987654
```

### 4. 3D 姿态窗口操作

- 鼠标拖动可旋转观察视角，滚轮缩放；
- 立方体随四元数转动，红/绿/蓝三轴为机体 X/Y/Z；
- 右上为 6 秒滚动窗口的 roll / pitch / yaw 曲线，右下为四元数、欧拉角与状态；
- 按 `z` 键把当前姿态重设为零位（先点击图形区域让窗口获得焦点）；
- 关闭窗口会停止采集线程并释放串口，`Ctrl+C` 也会经由 `finally` 释放。
