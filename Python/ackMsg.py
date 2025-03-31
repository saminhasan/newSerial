import struct

class AckMessage:
    @classmethod
    def from_bytes(cls, payload):
        raise NotImplementedError("Implement in subclass")

class AckHeartBeat(AckMessage):
    # ackID (1), timestamp (4)
    FORMAT = "<BI"
    KEYS = ["ackID", "timestamp"]

    @classmethod
    def from_bytes(cls, payload):
        values = struct.unpack(cls.FORMAT, payload)
        return dict(zip(cls.KEYS, values))

class AckReboot(AckMessage):
    # ackID (2), timestamp (4)
    FORMAT = "<BI"
    KEYS = ["ackID", "timestamp"]

    @classmethod
    def from_bytes(cls, payload):
        values = struct.unpack(cls.FORMAT, payload)
        return dict(zip(cls.KEYS, values))

class AckeStop(AckMessage):
    # ackID (3), timestamp (4)
    FORMAT = "<BI"
    KEYS = ["ackID", "timestamp"]

    @classmethod
    def from_bytes(cls, payload):
        values = struct.unpack(cls.FORMAT, payload)
        return dict(zip(cls.KEYS, values))

class AckMotorConfig(AckMessage):
    # ackID (4), axisID (1), armed (1), calibrated (1), timestamp (4)
    # Using 4 unsigned bytes then an unsigned int.
    FORMAT = "<5BI"
    KEYS = ["ackID", "axisID", "armed", "calibrated", "automatic","timestamp"]

    @classmethod
    def from_bytes(cls, payload):
        values = struct.unpack(cls.FORMAT, payload)
        result = dict(zip(cls.KEYS, values))
        # Convert armed and calibrated to boolean values
        result["armed"] = bool(result["armed"])
        result["calibrated"] = bool(result["calibrated"])
        result["automatic"] = bool(result["automatic"])
        return result

class AckMotorState(AckMessage):
    # ackID (5), axisID (1), temperature (1), then 5 floats, then timestamp (4)
    # FORMAT = "<BBb5fI"
    # KEYS = ["ackID", "axisID", "temperature", "positionSetpoint",
    #         "velocitySetpoint", "theta", "omega", "torque", "timestamp"]
    FORMAT = "<BB4fI"
    KEYS = ["ackID", "axisID", "positionSetpoint",
            "velocitySetpoint", "theta", "omega", "timestamp"]
    @classmethod
    def from_bytes(cls, payload):
        values = struct.unpack(cls.FORMAT, payload)
        return dict(zip(cls.KEYS, values))
        # return dict(zip(cls.KEYS, values))["positionSetpoint"]

class initPosition(AckMessage):
    # ackID (6), 6 floats for theta6, Idx (4), timestamp (4)
    FORMAT = "<B6fII"

    @classmethod
    def from_bytes(cls, payload):
        raw = struct.unpack(cls.FORMAT, payload)
        return {
            "ackID": raw[0],
            "theta6": list(raw[1:7]),
            "Idx": raw[7],
            "timestamp": raw[8]
        }

class trajectoryLength(AckMessage):
    # ackID (7), trajLen (4), timestamp (4)
    FORMAT = "<BII"
    KEYS = ["ackID", "trajLen", "timestamp"]

    @classmethod
    def from_bytes(cls, payload):
        values = struct.unpack(cls.FORMAT, payload)
        return dict(zip(cls.KEYS, values))

class feedRate(AckMessage):
    # ackID (8), feedRate (4), timestamp (4)
    FORMAT = "<BBI"
    KEYS = ["ackID", "feedRate", "timestamp"]

    @classmethod
    def from_bytes(cls, payload):
        values = struct.unpack(cls.FORMAT, payload)
        return dict(zip(cls.KEYS, values))

class trajectory6D(AckMessage):
    # ackID (9), rowFirst (6 floats), rowLast (6 floats), timestamp (4)
    FORMAT = "<B6f6fI"

    @classmethod
    def from_bytes(cls, payload):
        raw = struct.unpack(cls.FORMAT, payload)
        return {
            "ackID": raw[0],
            "rowFirst": list(raw[1:7]),
            "rowLast": list(raw[7:13]),
            "timestamp": raw[13]
        }

# Mapping of ackID to the corresponding message class.
MESSAGE_CLASSES = {
    1: AckHeartBeat,
    2: AckReboot,
    3: AckeStop,
    4: AckMotorConfig,
    5: AckMotorState,
    6: initPosition,
    7: trajectoryLength,
    8: feedRate,
    9: trajectory6D,
}

def parse_payload(payload: bytearray) -> dict:
    if not payload:
        raise ValueError("Empty payload")
    ack_id = payload[0]
    if ack_id not in MESSAGE_CLASSES:
        raise ValueError(f"Unknown ackID: {ack_id}")
    msg_class = MESSAGE_CLASSES[ack_id]
    return msg_class.from_bytes(payload)


# Example usage:
if __name__ == "__main__":
    # Example: create a test AckHeartBeat message with ackID=1 and timestamp=1234567890
    test_payload = bytearray(struct.pack("<BI", 1, 1234567890))
    message_dict = parse_payload(test_payload)
    print(message_dict)
