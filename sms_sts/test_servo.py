import serial
import time
import subprocess

# 1. Force Low Latency at the OS level for the Pi 5's ttyAMA10
try:
    # On Pi 5, serial0 usually points to ttyAMA10
    subprocess.run(['sudo', 'setserial', '/dev/serial0', 'low_latency'], check=True)
    print("SUCCESS: Low latency mode enabled")
except Exception as e:
    print(f"WARNING: Could not set low latency (check if setserial is installed): {e}")

# 2. Configure the Serial Port
try:
    ser = serial.Serial(
        port='/dev/serial0',
        baudrate=1000000,
        timeout=0.1, 
        write_timeout=0.5
    )
except Exception as e:
    print(f"ERROR: Could not open port: {e}")
    exit()

def send_ping(servo_id):
    # STS/SCS Ping Packet: FF FF [ID] [Len] [Instr] [Checksum]
    # Checksum = ~(ID + Length + Instruction) & 0xFF
    checksum = (~(servo_id + 0x02 + 0x01)) & 0xFF
    packet = bytearray([0xFF, 0xFF, servo_id, 0x02, 0x01, checksum])
    
    print(f"\n--- Testing ID: {servo_id} ---")
    print(f"Sending: {packet.hex().upper()}")
    
    ser.reset_input_buffer() # Clear anything sitting in the buffer
    ser.write(packet)
    ser.flush()              # Ensure data physically leaves the TX pin
    
    # Tiny pause for the automatic directional circuit on your board
    time.sleep(0.05) 
    
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting)
        print(f"RECEIVED: {response.hex().upper()}")
        if len(response) >= 6:
            # A valid response usually starts with FF FF
            print("RESULT: Servo responded! Hardware communication is working.")
        else:
            print("RESULT: Received data, but it's too short (potentially an echo).")
    else:
        print("RESULT: Total silence. No response.")

try:
    if ser.is_open:
        print("Serial port opened at 1,000,000 baud")
        
        # Test ID 1 (Standard default)
        for servo_id in range(1, 6):
          send_ping(servo_id)

        # Test ID 254 (Broadcast - every servo should answer)
        send_ping(254)

finally:
    ser.close()
    print("\nPort closed.")