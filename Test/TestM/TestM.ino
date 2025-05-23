#include "globals.h"
void setup()
{
  while (!Serial)
  {
    ;
  }
  parser.processPacketCallback = processPacket;
  if (CrashReport)
    logInfo(String(CrashReport).c_str());
  else
    logInfo("No CrashReport\n");


  logInfo("Waiting for all devices to connect...\n");
  myusb.begin();
  while (!(uSerial1 && uSerial2 && uSerial3))  //xx
  {
    myusb.Task();
    yield();
  }  //xx
  delay(1000);

  for (auto port : ports)
  {
    const char* serialnum = reinterpret_cast<const char*>(port->serialNumber());
    if (strcmp(serialnum, SN1) == 0)
      teensy1 = port;
    else if (strcmp(serialnum, SN2) == 0)
      teensy2 = port;
    else if (strcmp(serialnum, SN3) == 0)
      teensy3 = port;
  }
  logInfo("All devices assigned.\n");
  if (teensy1)
    logInfo("teensy1 SN: %s\n", reinterpret_cast<const char*>(teensy1->serialNumber()));
  else
    logInfo("teensy1 SN: (Not Assigned)");
  if (teensy2)
    logInfo("teensy2 SN: %s\n", reinterpret_cast<const char*>(teensy2->serialNumber()));
  else
    logInfo("teensy2 SN: (Not Assigned)");
  if (teensy3)
    logInfo("teensy3 SN: %s\n", reinterpret_cast<const char*>(teensy3->serialNumber()));
  else
    logInfo("teensy3 SN: (Not Assigned)");
  // add a while true loop here if init fails.
  ports[0] = teensy1;
  ports[1] = teensy2;
  ports[2] = teensy3;
  parser1.processPacketCallback = processFeedback;
  parser2.processPacketCallback = processFeedback;
  parser3.processPacketCallback = processFeedback;

  uint32_t uHostStartupTime = timer;
  logInfo("USB Host Startup Time: %.2f seconds\n", uHostStartupTime / 1e6);
  initTrackers();
  logInfo("<SYSID : 4 Ready>\n");
  motor_timer.begin(sendIRQ, 1000);
  // motor_timer.priority(255);
  timer = 0;
}

void loop()
{
  if (commandSent)
  {
    myusb.Task();
    pose6D pose(thetas[ArrayIndex]);
    pose.send(uSerial1);
    pose.send(uSerial2);
    pose.send(uSerial3);
    for (auto port : ports)
    {
      port->flush();
    }
    // logInfo("feedrates : %f | %f | %f | %f\n", fros[0], fros[1], fros[2], Combinedfro);

    commandSent = false;
  }
  tick();
  // cens();
  delayMicroseconds(50);
}
void tick()
{
  myusb.Task();
  if (uSerial1)
    parser1.parse();
  if (uSerial2)
    parser2.parse();
  if (uSerial3)
    parser3.parse();
}
void serialEvent()
{
  parser.parse();
}
void processFeedback(const uint8_t* p, uint32_t packetLength)
{
  uint8_t msgID = p[10];
  const uint8_t* payload = &p[11];
  const uint8_t payloadOffset = 11;
  uint8_t ackID = p[payloadOffset];

  if ((msgID == MSG_ACK) && (ackID == 5))
  {
    if (!automatic) return;

    AckMotorState ms;
    readPayload(ms, payload, sizeof(ms));
    axisFro[ms.axisID - 1] = calcFROpos(ms.theta);
    float actualError = ms.positionSetpoint - ms.theta;
    float predictedError = etArr[ms.axisID - 1]->update(ms.positionSetpoint);
    // float predictedError = etArr[ms.axisID - 1]->update(thetas[wrap_index(ArrayIndex+12, trajectoryLength)][ms.axisID - 1]);
    float rmse = rmseT[ms.axisID - 1]->update((actualError - predictedError));
    rmseAxis[ms.axisID - 1] = rmse;
    // modelFeedrate[ms.axisID - 1] = 100 * constrain((fabs(predictedError) + tol) / fabs(actualError), 0, 1);
    logInfo("T: %lu, ID:%u, u:%f, y:%f, CR: %f, PE: %f, RMSE: %f\n", ms.timestamp, ms.axisID, ms.positionSetpoint, ms.theta, ms.current, predictedError, rmse);
  }
  else
  {
    Serial.write(p, packetLength);
  }
}




void processPacket(const uint8_t* p, uint32_t packetLength)
{
  uint8_t sysId = p[9];


  switch (sysId)
  {
    case 0:
      processMsg(p, packetLength);
      routePacket(p, packetLength);
      break;
    case 4:
      processMsg(p, packetLength);
      break;
    default:
      routePacket(p, packetLength);
      break;
  }
}
void processMsg(const uint8_t* p, uint32_t packetLength)
{
  uint8_t sysId = p[9];
  uint8_t msgID = p[10];
  uint32_t payloadSize = packetLength - 16;
  const uint8_t* payload = &p[11];

  switch (msgID)
  {
    case MSG_STAGE_POSITION:
      {
        ArrayIndex = 0;  // idx
        pose6D Initpose(thetas[0]);
        Initpose.send(*teensy1);
        Initpose.send(*teensy2);
        Initpose.send(*teensy3);
        initPosition s;
        s.Idx = ArrayIndex;
        for (int i = 0; i < 6; ++i)
          s.theta6[i] = thetas[ArrayIndex][i];
        s.timestamp = micros();
        ACK ack(s);
        ack.send(Serial);
        break;
      }
    case MSG_MODE:
      {
        uint8_t modeVal;
        readPayload(modeVal, payload, payloadSize);
        automatic = (modeVal == 1);
        logInfo("AUTO: %s\n", automatic ? "ON" : "OFF");
        break;
      }

    case MSG_TRAJECTORY_LENGTH:
      {
        readPayload(trajectoryLength, payload, payloadSize);
        // logInfo("Trajectory Length: %u\n", trajectoryLength);
        trajectoryLengthS s;
        s.timestamp = micros();
        s.trajLen = trajectoryLength;
        ACK ack(s);
        ack.send(Serial);
        break;
      }
    case MSG_FEED_RATE:
      {
        readPayload(ufeedRate, payload, payloadSize);
        manFeed.setTarget((float)ufeedRate);
        // logInfo("uFeedrate: %u\n", ufeedRate);
        feedRateS s;
        s.timestamp = micros();
        s.feedRate = ufeedRate;
        ACK ack(s);
        ack.send(Serial);
        break;
      }
    case MSG_TRAJECTORY_6D:
      {
        readPayload(thetas, payload, payloadSize);
        dataReceived = true;
        ArrayIndex = 0;
        // logInfo("Trajectory [%lu]\n", (payloadSize / 4) / 6);
        // for (int i = 0; i < 5; i++)
        //   logInfo("thetas[%d]= [%f, %f, %f, %f, %f, %f]\n", i, thetas[i][0], thetas[i][1], thetas[i][2], thetas[i][3], thetas[i][4], thetas[i][5]);
        trajectory6D s;
        for (int i = 0; i < 6; ++i)
        {
          s.rowFirst[i] = thetas[0][i];
          s.rowLast[i] = thetas[trajectoryLength - 1][i];
        }
        s.timestamp = micros();
        ACK ack(s);
        ack.send(Serial);
        break;
      }
    case MSG_INFO:
      {
        logInfo("MSG_INFO\n");
        break;
      }
    default:
      if (sysId == 4)
        logInfo("NotImplementedError: 0x%X\n", msgID);  // NAK
      break;
  }
}
void routePacket(const uint8_t* fullPacket, uint32_t packetSize)
{
  uint8_t sysId = fullPacket[9];
  switch (sysId)
  {
    case 0:
      sendPacket(*teensy1, fullPacket, packetSize);
      sendPacket(*teensy2, fullPacket, packetSize);
      sendPacket(*teensy3, fullPacket, packetSize);
      // logInfo("Sending to All.\n");
      break;
    case 1:
      sendPacket(*teensy1, fullPacket, packetSize);
      // logInfo("Sending to 1.\n");

      break;
    case 2:
      sendPacket(*teensy2, fullPacket, packetSize);
      // logInfo("Sending to 2.\n");

      break;
    case 3:
      sendPacket(*teensy3, fullPacket, packetSize);
      // logInfo("Sending to 2.\n");

      break;
    default:
      logInfo("Sending to None?.\n");  //NAK

      break;
  }
}
template<typename T>
void readPayload(T& destination, const uint8_t* payload, uint32_t payloadSize)
{
  memcpy(&destination, payload, payloadSize);
}
template<typename T>
void sendPacket(T& port, const uint8_t* data, uint32_t size)
{
  if (!port)
  {
    Serial.println("Error: Null Port in sendPacket()");
    return;
  }
  port.write(data, size);
  port.flush();
}