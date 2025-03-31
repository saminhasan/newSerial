# General Control Bytes
NUL = 0x00  # Null character (NUL) - Represents a zero value

# Transmission Control Characters
SOH = 0x01  # Start of Heading (SOH) - Marks the start of a packet header
EOT = 0x04  # End of Transmission (EOT) - Indicates the end of an entire message

# Acknowledgment Control
ACK = 0x06  # Acknowledge (ACK) - Confirms successful reception of data
NAK = 0x15  # Negative Acknowledge (NAK) - Signals a transmission error or rejection

READ = 0x3F  # Read request ?
WRITE = 0x3D  # write request =
