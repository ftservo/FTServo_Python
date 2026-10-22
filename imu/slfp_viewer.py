#!/usr/bin/env python
#
# *********     SLFP Quaternion 3D Attitude Viewer      *********
#
# Poll the IMU SLFP quaternion at 50Hz and render the attitude with matplotlib 3D.
#
#   QX/QY/QZ : 16 bits half float(S1E5F10) at IMU_PRESENT_SLFP_QXL
#   QW       : sqrt(1 - QX^2 - QY^2 - QZ^2)
#
# Usage:
#   python imu/slfp_viewer.py                     # /dev/ttyUSB0, ID 200, 1000000 bps
#   python imu/slfp_viewer.py --port COM7 --id 1  # change port / IMU id
#   python imu/slfp_viewer.py --demo              # simulated attitude, no hardware
#   python imu/slfp_viewer.py --zero-on-start     # first second becomes the zero reference
#
# Requires : numpy, matplotlib (already installed), pyserial for a real device
#
# The serial reader runs in a background thread and publishes the latest sample,
# the matplotlib main thread only consumes that sample, so no blocking read ever
# happens inside a GUI callback.
#

import argparse
import math
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

# Make the project root(which contains scservo_sdk/) importable,
# independent of the current working directory
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scservo_sdk import PortHandler, COMM_SUCCESS
from scservo_sdk.imu import imu as ImuPacketHandler

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ---------------------------------------------------------------- configuration

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_IMU_ID = 200
DEFAULT_BAUD = 1000000

SAMPLE_PERIOD = 0.02                     # 20ms -> 50Hz reader thread
DISPLAY_INTERVAL_MS = 33                 # ~30fps matplotlib refresh

CURVE_WINDOW_S = 6.0                     # visible time span of the angle curves
CURVE_POINTS = int(CURVE_WINDOW_S / SAMPLE_PERIOD)

CUBE_HALF = 0.62                         # half size of the attitude cube
AXIS_LEN = 0.95                          # body axis length

# Sensor frame -> display frame. Keep the identity matrix if the cube turns the
# same way as the device. Use np.diag([-1.0, 1.0, 1.0]) to mirror X, etc.
AXIS_TRANSFORM = np.eye(3)

CUBE_COLOR = "#1f77b4"
ZERO_DELAY_S = 1.0                       # wait for the SFLP to settle (--zero-on-start)
AXIS_COLORS = ("#d62728", "#2ca02c", "#1f77b4")
AXIS_LABELS = ("X", "Y", "Z")
CURVE_COLORS = ("#d62728", "#2ca02c", "#1f77b4")
CURVE_LABELS = ("roll", "pitch", "yaw")


def _build_cube_segments(half: float) -> np.ndarray:
    """12 edges of a cube as one polyline, segments separated by NaN."""
    corners = np.array([[x, y, z]
                        for x in (-half, half)
                        for y in (-half, half)
                        for z in (-half, half)], dtype=float)
    edges = [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
             (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)]
    segments = []
    for first, second in edges:
        segments.append(corners[first])
        segments.append(corners[second])
        segments.append([np.nan, np.nan, np.nan])
    return np.array(segments, dtype=float)


CUBE_LINE = _build_cube_segments(CUBE_HALF)
BODY_AXES = np.array([[AXIS_LEN, 0.0, 0.0],
                      [0.0, AXIS_LEN, 0.0],
                      [0.0, 0.0, AXIS_LEN]], dtype=float)


# ---------------------------------------------------------------- math helpers

def normalize_quat(q) -> Optional[Tuple[float, float, float, float]]:
    """Normalize (x, y, z, w). Returns None when the vector is not usable.

    scs_slfp_qw() returns 0.0 when QX^2 + QY^2 + QZ^2 > 1, so the raw quaternion
    may be far from unit length; normalizing keeps the rotation matrix orthogonal.
    """
    arr = np.asarray(q, dtype=float)
    norm = float(np.linalg.norm(arr))
    if not np.isfinite(norm) or norm < 1e-9:
        return None
    arr = arr / norm
    return (float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3]))


def quat_to_matrix(q) -> np.ndarray:
    """Unit quaternion (x, y, z, w) -> 3x3 rotation matrix."""
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array([
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
        [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
        [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
    ], dtype=float)


def quat_to_euler(q) -> Tuple[float, float, float]:
    """Unit quaternion -> (roll, pitch, yaw) in degrees, ZYX order."""
    x, y, z, w = q
    sin_pitch = 2.0 * (w * y - z * x)
    sin_pitch = max(-1.0, min(1.0, sin_pitch))       # clamp, asin() domain
    roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = math.asin(sin_pitch)
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return (math.degrees(roll), math.degrees(pitch), math.degrees(yaw))


def euler_to_quat(roll_deg: float, pitch_deg: float, yaw_deg: float):
    """(roll, pitch, yaw) in degrees -> quaternion (x, y, z, w)."""
    half_roll = math.radians(roll_deg) * 0.5
    half_pitch = math.radians(pitch_deg) * 0.5
    half_yaw = math.radians(yaw_deg) * 0.5
    cr, sr = math.cos(half_roll), math.sin(half_roll)
    cp, sp = math.cos(half_pitch), math.sin(half_pitch)
    cy, sy = math.cos(half_yaw), math.sin(half_yaw)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


def quat_multiply(a, b) -> Tuple[float, float, float, float]:
    """Hamilton product a x b: rotation b is applied first, then rotation a."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def quat_conjugate(q) -> Tuple[float, float, float, float]:
    """Inverse rotation of a unit quaternion."""
    x, y, z, w = q
    return (-x, -y, -z, w)


# ---------------------------------------------------------------- sample model

@dataclass
class AttitudeSample:
    """One reading of the IMU attitude."""
    q_raw: Tuple[int, int, int]                        # raw QX/QY/QZ half float bits
    q: Optional[Tuple[float, float, float, float]]     # normalized (x, y, z, w)
    euler: Optional[Tuple[float, float, float]]        # roll/pitch/yaw in degrees
    stamp: float                                       # time.time()
    status: str                                        # "OK" / demo / error text


# ---------------------------------------------------------------- data sources

class ImuReader:
    """Read the SLFP quaternion at 50Hz in a background thread."""

    def __init__(self, port: str, imu_id: int, baud: int):
        self.port = port
        self.imu_id = imu_id
        self.baud = baud
        self._port_handler = PortHandler(port)
        self._packet = ImuPacketHandler(self._port_handler)
        self._lock = threading.Lock()
        self._latest = None
        self._stop_event = threading.Event()
        self._thread = None
        self._closed = False
        self.error_count = 0

    # -- lifecycle ---------------------------------------------------------
    def open(self) -> None:
        try:
            opened = self._port_handler.openPort()
        except Exception as exc:
            raise RuntimeError("Failed to open %s: %s" % (self.port, exc)) from exc
        if not opened:
            raise RuntimeError("Failed to open %s" % self.port)
        if not self._port_handler.setBaudRate(self.baud):
            self._port_handler.closePort()
            raise RuntimeError("Failed to change the baudrate to %d" % self.baud)
        print("Succeeded to open %s" % self.port)
        print("Succeeded to change the baudrate to %d" % self.baud)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, name="imu-reader", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)
        self._thread = None

    def close(self) -> None:
        self.stop()
        if self._closed:
            return
        self._closed = True
        try:
            self._port_handler.closePort()
            print("Closed %s" % self.port)
        except Exception:
            pass

    # -- consumer side -----------------------------------------------------
    def latest(self) -> Optional[AttitudeSample]:
        with self._lock:
            return self._latest

    # -- producer side -----------------------------------------------------
    def _loop(self) -> None:
        while not self._stop_event.is_set():
            cycle_start = time.time()
            qx, qy, qz, qw, result, error = self._packet.readSlfp(self.imu_id)
            if result == COMM_SUCCESS:
                q = normalize_quat((
                    self._packet.scs_halffloat(qx),
                    self._packet.scs_halffloat(qy),
                    self._packet.scs_halffloat(qz),
                    qw,
                ))
                euler = quat_to_euler(q) if q is not None else None
                status = "OK" if not error else self._packet.getRxPacketError(error)
            else:
                # keep the previous attitude on screen, only update the status text
                q = None
                euler = None
                status = self._packet.getTxRxResult(result)
                self.error_count += 1

            with self._lock:
                self._latest = AttitudeSample((qx, qy, qz), q, euler, time.time(), status)

            delay = SAMPLE_PERIOD - (time.time() - cycle_start)
            self._stop_event.wait(delay if delay > 0 else 0.0)


class DemoAttitudeSource:
    """Simulated attitude with the same interface as ImuReader (--demo)."""

    def __init__(self) -> None:
        self._t0 = time.time()

    def latest(self) -> AttitudeSample:
        t = time.time() - self._t0
        roll = 25.0 * math.sin(2.0 * math.pi * 0.25 * t)
        pitch = 18.0 * math.sin(2.0 * math.pi * 0.40 * t + 0.7)
        yaw = (t * 45.0) % 360.0
        q = euler_to_quat(roll, pitch, yaw)
        return AttitudeSample((0, 0, 0), q, (roll, pitch, yaw), time.time(), "DEMO")

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def close(self) -> None:
        pass


# ---------------------------------------------------------------- viewer

class AttitudeViewer:
    """matplotlib 3D attitude panel + euler angle curves + numeric overlay."""

    def __init__(self, source, title: str = "IMU SLFP Attitude",
                 zero_on_start: bool = False):
        self._source = source
        self._anim = None
        self._zero_q = None                  # captured reference attitude
        self._zero_on_start = zero_on_start
        self._zero_deadline = None

        self._fig = plt.figure(figsize=(12.5, 7.0))
        try:
            self._fig.canvas.manager.set_window_title(title)
        except Exception:
            pass
        self._fig.suptitle(title, fontsize=13)

        self._ax3d = self._fig.add_axes([0.00, 0.02, 0.50, 0.90], projection="3d")
        self._ax_curve = self._fig.add_axes([0.57, 0.58, 0.39, 0.32])
        self._ax_info = self._fig.add_axes([0.57, 0.06, 0.39, 0.44])

        self._init_scene()
        self._init_curves()
        self._init_info()

    # -- scene -------------------------------------------------------------
    def _init_scene(self) -> None:
        ax = self._ax3d
        limit = 1.45
        ax.set_xlim(-limit, limit)
        ax.set_ylim(-limit, limit)
        ax.set_zlim(-limit, limit)
        ax.set_box_aspect((1, 1, 1))
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.view_init(elev=22, azim=-58)
        ax.grid(True)
        ax.plot([0.0], [0.0], [0.0], marker="o", color="#444444", markersize=4)

        self._cube_line, = ax.plot([], [], [], color=CUBE_COLOR, linewidth=1.8)

        self._axis_lines = []
        self._axis_labels = []
        for color, label in zip(AXIS_COLORS, AXIS_LABELS):
            line, = ax.plot([], [], [], color=color, linewidth=2.4)
            text = ax.text(0.0, 0.0, 0.0, label, color=color, fontsize=12,
                           fontweight="bold")
            self._axis_lines.append(line)
            self._axis_labels.append(text)

    # -- curves ------------------------------------------------------------
    def _init_curves(self) -> None:
        ax = self._ax_curve
        ax.set_xlim(-CURVE_WINDOW_S, 0.0)
        ax.set_ylim(-180.0, 180.0)
        ax.set_xlabel("time [s]")
        ax.set_ylabel("angle [deg]")
        ax.grid(True, alpha=0.3)

        self._stamps = np.full(CURVE_POINTS, np.nan)
        self._angles = np.full((3, CURVE_POINTS), np.nan)
        self._curve_lines = []
        for color, label in zip(CURVE_COLORS, CURVE_LABELS):
            line, = ax.plot([], [], color=color, linewidth=1.2, label=label)
            self._curve_lines.append(line)
        ax.legend(loc="upper right", fontsize=8, ncols=3)

    # -- numeric overlay ---------------------------------------------------
    def _init_info(self) -> None:
        ax = self._ax_info
        ax.set_axis_off()
        ax.set_title("quaternion / euler angles", fontsize=10, loc="left")
        self._info_text = ax.text(0.0, 0.96, "", va="top", ha="left",
                                  family="monospace", fontsize=10.5,
                                  transform=ax.transAxes)

    # -- per frame ---------------------------------------------------------
    def _update(self, _frame):
        sample = self._source.latest()
        if sample is not None:
            if self._zero_on_start and self._zero_q is None and sample.q is not None:
                if self._zero_deadline is None:
                    self._zero_deadline = sample.stamp + ZERO_DELAY_S
                elif sample.stamp >= self._zero_deadline:
                    self.capture_zero(sample)
            self._render(sample)
        return self._cube_line,

    def capture_zero(self, sample) -> bool:
        """Use the given sample as the zero reference and restart the curves."""
        if sample is None or sample.q is None:
            return False
        self._zero_q = sample.q
        self._zero_deadline = None
        self._stamps[:] = np.nan
        self._angles[:] = np.nan
        return True

    def _display_quat(self, q):
        """Apply the captured zero reference; no zero means absolute attitude."""
        if self._zero_q is None:
            return q
        relative = quat_multiply(quat_conjugate(self._zero_q), q)
        return normalize_quat(relative) or relative

    def _render(self, sample: AttitudeSample) -> None:
        display_q = None
        euler = None
        if sample.q is not None:
            display_q = self._display_quat(sample.q)
            if self._zero_q is None and sample.euler is not None:
                euler = sample.euler
            else:
                euler = quat_to_euler(display_q)

            rotation = AXIS_TRANSFORM @ quat_to_matrix(display_q)
            cube = CUBE_LINE @ rotation.T
            self._cube_line.set_data_3d(cube[:, 0], cube[:, 1], cube[:, 2])

            for index, vector in enumerate(BODY_AXES):
                tip = rotation @ vector
                self._axis_lines[index].set_data_3d(
                    [0.0, float(tip[0])],
                    [0.0, float(tip[1])],
                    [0.0, float(tip[2])],
                )
                self._axis_labels[index].set_position_3d(
                    (float(tip[0]) * 1.10, float(tip[1]) * 1.10, float(tip[2]) * 1.10)
                )

            if euler is not None:
                self._push_angles(euler, sample.stamp)
                self._refresh_curves(sample.stamp)

        self._info_text.set_text(self._format_info(sample, display_q, euler))

    def _push_angles(self, euler, stamp: float) -> None:
        """Shift the ring buffers by one slot and append the new sample."""
        self._angles[:, :-1] = self._angles[:, 1:]
        self._angles[:, -1] = euler
        self._stamps[:-1] = self._stamps[1:]
        self._stamps[-1] = stamp

    def _refresh_curves(self, now: float) -> None:
        x = self._stamps - now
        for index, line in enumerate(self._curve_lines):
            line.set_data(x, self._angles[index])

    def _format_info(self, sample: AttitudeSample, display_q, euler) -> str:
        qx, qy, qz = sample.q_raw
        lines: List[str] = []
        if display_q is None:
            lines.append("quaternion : --")
        else:
            x, y, z, w = display_q
            lines.append("QX %+8.4f   QY %+8.4f" % (x, y))
            lines.append("QZ %+8.4f   QW %+8.4f" % (z, w))
            lines.append("raw QX 0x%04X  QY 0x%04X  QZ 0x%04X" % (qx, qy, qz))
        lines.append("")
        if euler is None:
            lines.append("roll / pitch / yaw : --")
        else:
            roll, pitch, yaw = euler
            lines.append("roll  %+9.2f deg" % roll)
            lines.append("pitch %+9.2f deg" % pitch)
            lines.append("yaw   %+9.2f deg" % yaw)
        lines.append("")
        if self._zero_q is None:
            lines.append("reference : absolute   (press z to zero)")
        else:
            lines.append("reference : relative to captured zero")
        lines.append("status : %s" % sample.status)
        return "\n".join(lines)

    # -- run ---------------------------------------------------------------
    def show(self) -> None:
        self._fig.canvas.mpl_connect("close_event", self._on_close)
        self._fig.canvas.mpl_connect("key_press_event", self._on_key)
        self._anim = FuncAnimation(self._fig, self._update,
                                   interval=DISPLAY_INTERVAL_MS,
                                   blit=False, cache_frame_data=False)
        plt.show()

    def _on_close(self, _event) -> None:
        self._source.stop()

    def _on_key(self, event) -> None:
        if event.key == "z":
            self.capture_zero(self._source.latest())


# ---------------------------------------------------------------- entry point

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read the IMU SLFP quaternion and show the attitude in 3D")
    parser.add_argument("--port", default=DEFAULT_PORT,
                        help="serial port, e.g. COM6 (default: %(default)s)")
    parser.add_argument("--id", type=int, default=DEFAULT_IMU_ID, dest="imu_id",
                        help="IMU id on the bus (default: %(default)s)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD,
                        help="bus baudrate (default: %(default)s)")
    parser.add_argument("--demo", action="store_true",
                        help="show a simulated attitude without hardware")
    parser.add_argument("--zero-on-start", action="store_true",
                        help="use the attitude after %g s as the zero reference"
                             % ZERO_DELAY_S)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.demo:
        source = DemoAttitudeSource()
        title = "IMU SLFP Attitude  [DEMO]"
    else:
        source = ImuReader(args.port, args.imu_id, args.baud)
        source.open()
        source.start()
        title = "IMU SLFP Attitude  %s  ID %d" % (args.port, args.imu_id)

    try:
        AttitudeViewer(source, title, zero_on_start=args.zero_on_start).show()
    except KeyboardInterrupt:
        pass
    finally:
        source.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
