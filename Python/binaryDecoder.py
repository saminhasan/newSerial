import os
import zlib
import logging
import struct
from datetime import datetime
from ackMsg import parse_payload

# Setup logging once, at startup
time_string = datetime.now().replace(microsecond=0).isoformat().replace(":", "-")
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_filename = f"log_{time_string}.log"
log_file = os.path.join(log_dir, log_filename)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w"),
        # logging.StreamHandler()  # Uncomment if you want console output too
    ],
)
logger = logging.getLogger("SerialLogger")
logger.info("Logger started.")

# Constants matching your Teensy packet format.
PACKET_START = 0x01
PACKET_END   = 0x04

# Message IDs – update these if needed to match your definitions.

MSG_HEARTBEAT = 0
MSG_REBOOT = 2
MSG_ESTOP = 4
MSG_ENABLE = 6
MSG_DISABLE = 8
MSG_CALIBRATE = 10
MSG_STAGE_POSITION = 12
MSG_MODE = 14
MSG_POSITION6D = 16
MSG_TRAJECTORY_LENGTH = 18
MSG_FEED_RATE = 20
MSG_TRAJECTORY_6D = 22
MSG_INFO = 24
MSG_ACK = 32

def parse_packets(buffer: bytes, rx_queue) -> bytes:
    """
    Scan through the binary buffer and process complete packets.
    
    Args:
      buffer (bytes): Incoming binary data.
      rx_queue: A queue (e.g. from multiprocessing or queue module) to which text
                messages (like INFO messages) are added.
    
    Returns:
      Remaining unprocessed data (if a partial packet remains).
    """
    pos = 0
    buffer_len = len(buffer)
    while buffer_len - pos >= 16:
        # Check for start byte.
        if buffer[pos] != PACKET_START:
            pos += 1
            continue
        # Get packet length from bytes 1-4 (little-endian).
        if buffer_len - pos < 5:
            break
        packetLength = int.from_bytes(buffer[pos+1:pos+5], 'little')
        if packetLength < 16 or packetLength > (buffer_len - pos):
            pos += 1
            continue
        # Verify end byte.
        if buffer[pos + packetLength - 1] != PACKET_END:
            pos += 1
            continue
        # Get the reported CRC from bytes (packetLength-5) to (packetLength-1).
        crc_reported = int.from_bytes(buffer[pos+packetLength-5:pos+packetLength-1], 'little')
        # Compute CRC over bytes [1, packetLength-5) (excludes start, CRC field, and end).
        crc_computed = zlib.crc32(buffer[pos+1:pos+packetLength-5]) & 0xffffffff
        if crc_reported != crc_computed:
            print("CRC Mismatch")
            pos += 1
            continue
        # Process the complete packet.
        process_msg(buffer[pos:pos+packetLength], rx_queue)
        pos += packetLength
    return buffer[pos:]




import struct
import zlib

def process_msg(packet: bytes, rx_queue) -> None:
    start_byte = packet[0]
    end_byte = packet[-1]

    packet_length, = struct.unpack_from("<I", packet, 1)
    sequence_number, = struct.unpack_from("<I", packet, 5)
    sys_id = packet[9]
    msg_id = packet[10]
    payload = packet[11:-5]
    crc_received, = struct.unpack_from("<I", packet, len(packet) - 5)
    crc_computed = zlib.crc32(packet[1:-5])

    if msg_id == MSG_INFO:
        text = payload.rstrip(b'\x00').decode('utf-8', errors='ignore')
        payload_str = f"Text: {text}"
        logger.info(f"[INFO MSG] {text}")


    elif msg_id == MSG_ACK:
        payload_str = f"ACK : {parse_payload(payload=payload)}\n"
    else:
        payload_str = f"(Unknown msgID=0x{msg_id:02X}) Raw: " + ' '.join(f'0x{b:02X}' for b in payload)

    msg = (
        f"\n"
        f"  Packet Received:\n"
        f"  Start Byte       : 0x{start_byte:02X}\n"
        f"  Packet Length    : {packet_length} bytes\n"
        f"  Sequence Number  : {sequence_number}\n"
        f"  System ID        : {sys_id}\n"
        f"  Message ID       : {msg_id}\n"
        f"  Payload Length   : {len(payload)} bytes\n"
        f"  Payload          : {payload_str}"
        f"  CRC Match        : {'Yes' if crc_received == crc_computed else 'No'}\n"
        f"  End Byte         : 0x{end_byte:02X}\n"
    )
    if not (start_byte == 0x01 and end_byte == 0x04 and crc_received == crc_computed):
        msg += f"\n  \tPacket   Type    : Invalid"

    rx_queue.put(msg + "\n")


# --- Example Usage in a Serial Process ---
# The following snippet shows how you might integrate this into a process
# that continuously reads from a serial port and uses a byte buffer.

import time
import serial  # pyserial
from queue import Queue

def serial_comm_process(port: str, rx_queue: Queue, tx_queue: Queue) -> None:
    """
    Opens the serial port and continuously reads binary data,
    parsing complete packets and pushing INFO messages to rx_queue.
    """
    ser = serial.Serial(port, baudrate=115200, timeout=0)
    buffer = b""
    
    while True:
        # Write any outgoing data.
        while not tx_queue.empty():
            outgoing_data = tx_queue.get()
            ser.write(outgoing_data)
        
        # Read available binary data.
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting)
        
        # Parse complete packets and update the buffer with leftover data.
        buffer = parse_packets(buffer, rx_queue)
        
        time.sleep(0.0005)  # sleep briefly

