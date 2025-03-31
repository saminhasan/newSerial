#ifndef GLOBALS_H
#define GLOBALS_H
elapsedMicros timer;
#include <messages.h>
#include <USBHost_t36.h>
#include <packetParser.hpp>

#define N 10000
#define U_BUFFER_SIZE 32768
#define INPUT_BUFFER_SIZE 240016


uint8_t USBBuffer[INPUT_BUFFER_SIZE];
DMAMEM uint8_t uSerialBuffer1[U_BUFFER_SIZE];
DMAMEM uint8_t uSerialBuffer2[U_BUFFER_SIZE];
DMAMEM uint8_t uSerialBuffer3[U_BUFFER_SIZE];

const uint8_t sysID = 4;
// constexpr const char* SN1 = "15724840";
// constexpr const char* SN2 = "17016000";
// constexpr const char* SN3 = "17017360";
constexpr const char* SN1 = "11304080";
constexpr const char* SN2 = "17015970";
constexpr const char* SN3 = "17016690";

bool dataReceived = false;
volatile uint32_t ArrayIndex = 0;
bool automatic = false;
uint32_t trajectoryLength = N;
DMAMEM float thetas[N][6];
IntervalTimer motor_timer;
volatile bool commandSent = false;
//////////////////////////
// Motor control parameters
volatile uint32_t frRemainder = 0;
uint8_t feedRate = 0;
uint8_t fro = 0;
const uint32_t frMax = 100;


USBHost myusb;
USBHub hub1(myusb);
USBHub hub2(myusb);
USBHub hub3(myusb);

USBSerial_BigBuffer uSerial1(myusb, 1);
USBSerial_BigBuffer uSerial2(myusb, 2);
USBSerial_BigBuffer uSerial3(myusb, 3);

USBSerial_BigBuffer* teensy1 = nullptr;
USBSerial_BigBuffer* teensy2 = nullptr;
USBSerial_BigBuffer* teensy3 = nullptr;

USBSerial_BigBuffer* ports[] = { &uSerial1, &uSerial2, &uSerial3 };


PacketParser<usb_serial_class> parser(Serial, USBBuffer, INPUT_BUFFER_SIZE);
// void processPacket(const uint8_t* p, uint32_t packetLength);
PacketParser<USBSerial_BigBuffer> parser1(uSerial1, uSerialBuffer1, U_BUFFER_SIZE);
PacketParser<USBSerial_BigBuffer> parser2(uSerial2, uSerialBuffer2, U_BUFFER_SIZE);
PacketParser<USBSerial_BigBuffer> parser3(uSerial3, uSerialBuffer3, U_BUFFER_SIZE);

void sendIRQ()
{
  if (!(dataReceived && automatic))  // add armed or not chaeck here.
    return;
  // get multiple feedrate here take the min.
  frRemainder += fro;
  uint32_t deltaIndex = floor(frRemainder / frMax);
  frRemainder %= frMax;
  ArrayIndex = (ArrayIndex + deltaIndex) % trajectoryLength;
  commandSent = true;
}
#endif
