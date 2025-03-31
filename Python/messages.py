from __future__ import annotations
from serializer import Serializer
from zlib import crc32
import numpy as np
import struct

# Packet format:
# startByte(1) - packetLength(4) - sequenceNumber(4) - sysID(1) - msgID(1) - message(N) - CRC32(4) - endByte(1)
# (16-byte overhead + payload)

class Packet:
    _sequenceNumber: np.uint32 = 0  # class-level counter

    def __init__(self, sysID, msgID, message):
        self.sysID: np.uint8 = np.uint8(sysID)
        self.msgID: np.uint8 = np.uint8(msgID)
        # Serialize the payload using Serializer
        self.serializer = Serializer(message)
        # Pack sysID (1 byte) + msgID (1 byte) + serialized payload
        payload = struct.pack("<BB", self.sysID, self.msgID) + self.serializer.pack()
        self.msgLen = self.serializer.size
        
        # Build packet header and trailer
        self.startByte: np.uint8 = np.uint8(0x01)
        self.packetLength: np.uint32 = np.uint32(16 + self.msgLen)  # total packet length
        self.sequenceNumber: np.uint32 = np.uint32(Packet._sequenceNumber + 1)
        self.header: bytes = struct.pack("<BII", self.startByte, self.packetLength, self.sequenceNumber)
        self.checksum: int = crc32(self.header[1:] + payload)
        self.endByte: np.uint8 = np.uint8(0x04)
        self.rawBytes: bytes = self.header + payload + struct.pack("<IB", self.checksum, self.endByte)
        self.fmt = "<BII"+ self.serializer.format_string[1:] +"IB"
        # print(self.fmt)
        Packet._sequenceNumber += 1

    def __repr__(self):
        return (
            # f"{self.__class__.__name__}("
            # f"startByte=0x{self.rawBytes[0]:02X}, "
            # f"packetLength={int.from_bytes(self.rawBytes[1:5], 'little')}, "
            # f"sequenceNumber={int.from_bytes(self.rawBytes[5:9], 'little')}, "
            # f"sysID={int(self.rawBytes[9])}, "
            # f"msgID={int(self.rawBytes[10])}, "
            # f"message=[{' '.join(f'0x{byte:02X}' for byte in self.rawBytes[11:-5])}], "
            # f"checksum=0x{int.from_bytes(self.rawBytes[-5:-1], 'little'):08X}, "
            # f"endByte=0x{self.rawBytes[-1]:02X})\n"
            f"{' '.join(f'0x{byte:02X}' for byte in self.rawBytes)}"
        )

# Specific message types are now thin wrappers that directly construct a Packet.
class HeartBeat(Packet):
    def __init__(self):
        super().__init__(sysID=0, msgID=0, message=None)

class Reboot(Packet):
    def __init__(self):
        super().__init__(sysID=0, msgID=2, message=None)

class eStop(Packet):
    def __init__(self):
        super().__init__(sysID=0, msgID=4, message=None)

class Enable(Packet):
    def __init__(self):
        super().__init__(sysID=0, msgID=6, message=None)

class Disable(Packet):
    def __init__(self):
        super().__init__(sysID=0, msgID=8, message=None)

class Calibrate(Packet):
    def __init__(self):
        super().__init__(sysID=0, msgID=10, message=None)

class Mode(Packet):
    def __init__(self, value: np.uint8 = np.uint8(0x00)):
        super().__init__(sysID=0, msgID=14, message=np.uint8(value))

class pose6D(Packet):
    def __init__(self, value: np.ndarray = np.array([0., 0., 0., 0., 0., 0.], dtype=np.float32)):
        super().__init__(sysID=0, msgID=16, message=value)

class stagePosition(Packet):
    def __init__(self):
        super().__init__(sysID=4, msgID=12, message=None)

class TrajectoryLength(Packet):
    def __init__(self, value: np.uint32 = np.uint32(0)):
        super().__init__(sysID=4, msgID=18, message=np.uint32(value))

class FeedRate(Packet):
    def __init__(self, value: np.uint8 = np.uint8(100)):
        super().__init__(sysID=4, msgID=20, message=np.uint8(value))

class Trajectory6D(Packet):
    def __init__(self, value: np.ndarray = np.tile(
        np.sin(np.linspace(0, 2 * np.pi, 1000, endpoint=False, dtype=np.float32))[:, None],
        (1, 6)
    )):
        super().__init__(sysID=4, msgID=22, message=value)

class Info(Packet):
    def __init__(self, sysID: np.uint8, value: str = " "):
        super().__init__(sysID=sysID, msgID=24, message=str(value))

   

def test():
    test_cases = [
    HeartBeat(),
    Reboot(),
    eStop(),
    Enable(),
    Disable(),
    Calibrate(),
    stagePosition(),
    Mode(value=np.uint8(2)),
    pose6D(),
    TrajectoryLength(value=np.uint32(987654321)),
    FeedRate(value=np.uint8(77)),
    Trajectory6D(value=np.array([1, 2, 3, 4, 5, 6], dtype=np.float32)),
    Info(sysID=np.uint8(3), value=f"OK{np.pi:.6f}"),
    ]
    for msg in test_cases:
        # print(f"\nMessage: {msg}")
        # print(f"\nPacket: {msg.rawBytes}")
        print(f"{msg}")

if __name__ == '__main__':
    test()



