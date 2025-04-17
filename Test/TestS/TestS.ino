#include "globals.h"

void setup()
{
  while (!Serial)
  {
    ;
  }
  if (CrashReport)
    logInfo(String(CrashReport).c_str());
  else
    logInfo("No CrashReport\n");
  parser.processPacketCallback = processPacket;
  switch (teensySerialNumber)
  {
    case ID1: sysID = 1; break;
    case ID2: sysID = 2; break;
    case ID3: sysID = 3; break;
  }
  Packet::sysID = sysID;
  AXIS_L = 2 * sysID - 1;
  AXIS_R = 2 * sysID + 0;
  motor1.setAxisID(AXIS_L);
  motor2.setAxisID(AXIS_R);
  logInfo("<sysID : %d | Serial Number : %lu | AxisL : %u| AxisR : %u>\n", sysID, teensySerialNumber, AXIS_L, AXIS_R);
  ////////////////////////////
  motor1.init();
  motor2.init();
  eStop_motor();
  motor_timer.begin(sendCmd, 1000);
  ///////////////////////////
}
void sendCmd()
{
  motor1.tick();
  motor2.tick();
}
void eStop_motor()
{
  motor1.setVelocity(0);
  motor2.setVelocity(0);
  motor1.disable();
  motor2.disable();
}
void loop()
{
  if (motor1.newConfig || motor1.newState)
    motor1.update();
  delayMicroseconds(1);
  if (motor2.newConfig || motor2.newState)
    motor2.update();
  cens();
  delayMicroseconds(1);
}

void serialEvent()
{
  parser.parse();
}

void processPacket(const uint8_t* p, uint32_t packetLength)
{
  // uint8_t startByte = p[0];
  // uint32_t len = p[1] | (p[2] << 8) | (p[3] << 16) | (p[4] << 24);
  // uint32_t sequenceNum = p[5] | (p[6] << 8) | (p[7] << 16) | (p[8] << 24);
  // uint8_t sysID = p[9];
  // uint8_t msgID = p[10];
  // uint32_t msgSize = packetLength - 16;
  // uint32_t crc32 = p[packetLength - 5] | (p[packetLength - 4] << 8) | (p[packetLength - 3] << 16) | (p[packetLength - 2] << 24);
  // uint8_t endByte = p[packetLength - 1];
  // logInfo("SOT:0x%02X LEN:%lu SEQ:%lu SYS:%u MSG:%u MSGLEN:%u CRC:0x%08lX EOT:0x%02X\n",
  //         startByte, len, sequenceNum, sysID, msgID, msgSize, crc32, endByte);
  processMsg(p, packetLength);
}
void processMsg(const uint8_t* p, uint32_t packetLength)
{

  uint8_t sysId = p[9];
  uint8_t msgID = p[10];
  uint32_t payloadSize = packetLength - 16;
  const uint8_t* payload = &p[11];

  switch (msgID)
  {
    case MSG_ENABLE:
      {
        // logInfo("ENABLE\n");  // ack motorConfig
        motor1.setVelocity(0);
        motor2.setVelocity(0);
        motor1.enable();
        motor2.enable();
        break;
      }
    case MSG_DISABLE:
      {
        // logInfo("DISABLE\n");  // ack motorConfig
        motor1.setVelocity(0);
        motor2.setVelocity(0);
        motor1.disable();
        motor2.disable();
        break;
      }
    case MSG_CALIBRATE:
      {
        // uint8_t calibrateVal = 0;
        // readPayload(calibrateVal, payload, payloadSize);
        // logInfo("CALIBRATE\n");  // ack motorConfig

        if ((motor1.cState == 0) && (motor2.cState == 0))
        {
          motor1.tState += 1;
          motor2.tState += 1;
          return;
        }
        else if (motor1.cState < 4)
        {
          motor1.tState += 1;
          return;
        }
        else if (motor2.cState < 4)
        {
          motor2.tState += 1;
          return;
        }
        else
        {
          motor1.tState += 1;
          motor2.tState += 1;
          return;
        }
        break;
      }
    case MSG_MODE:
      {
        uint8_t modeVal;
        readPayload(modeVal, payload, payloadSize);
        automatic = (modeVal == 1);
        // logInfo("modeVal : %u\n", modeVal);
        // logInfo("AUTO: %s\n", automatic ? "ON" : "OFF");  // ack motorConfig

        motor1.setMode(automatic);
        motor2.setMode(automatic);
        break;
      }

    case MSG_POSITION6D:
      {
        float theta[6];
        readPayload(theta, payload, payloadSize);
        // logInfo("POSITION6D : %f, %f,  %f, %f, %f, %f\n", theta[0], theta[1], theta[2], theta[3], theta[4], theta[5]);  // ack motorState
        // logInfo("L : %f | R : %f\n", theta[AXIS_L - 1], theta[AXIS_R - 1]);                                             // ack motorState
        motor1.setPositionSetpoint(theta[AXIS_L - 1]);
        motor2.setPositionSetpoint(theta[AXIS_R - 1]);
        break;
      }
    default:
      if ((sysId == sysID) || (sysId == 0))
        logInfo("NotImplementedError: 0x%X\n", msgID);
      else
        logInfo("Ignored - %u", sysID);
      break;
  }
}

template<typename T>
void readPayload(T& destination, const uint8_t* payload, uint32_t payloadSize)
{
  memcpy(&destination, payload, sizeof(T));
}

void ext_output1(const CAN_message_t& msg)
{
  if (msg.bus == 1)
    motor1.CanRxHandler(msg);
  if (msg.bus == 2)
    motor2.CanRxHandler(msg);
}