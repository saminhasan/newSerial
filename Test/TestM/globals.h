#ifndef GLOBALS_H
#define GLOBALS_H
elapsedMicros timer;
#include <FroCtrl.h>
#include <messages.h>
#include <USBHost_t36.h>
#include <packetParser.hpp>
#include "tracker.h"
#include "rmse.h"
#define N 12001
#define U_BUFFER_SIZE 16384
#define INPUT_BUFFER_SIZE 288100


uint8_t USBBuffer[INPUT_BUFFER_SIZE];
DMAMEM uint8_t uSerialBuffer1[U_BUFFER_SIZE];
DMAMEM uint8_t uSerialBuffer2[U_BUFFER_SIZE];
DMAMEM uint8_t uSerialBuffer3[U_BUFFER_SIZE];

const uint8_t sysID = 4;
// constexpr const char* SN1 = "15724840";
// constexpr const char* SN2 = "17016000";
// constexpr const char* SN3 = "17017360";
constexpr const char* SN1 = "15724840";//11304080";
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
uint8_t ufeedRate = 0;
uint8_t fro = 0;
const uint32_t frMax = 100;
float axisFro[6] = { 0.0 };
float modelFeedrate[6] = { 0.0 };
float rmseAxis[6] = { 0.0 };
const float zeta = 1.0;
const float w_n = 2 * M_PI * 15;
const float phi = 2 * zeta / w_n;
const float tol = 2 * M_PI / 4096 * 4;  //?
// bool axisHaltFlag[6] = { true };/// do this frim insdie class.
//////////////////////////
FeedrateGovernor manFeed(0, 32.0f, 100);
const int order = 2;
float bCoeffs[order + 1] = { 0.9976f, -1.8997f, 0.9021f };
float aCoeffs[order + 1] = { 1.0000f, -1.8949f, 0.9045f };
ErrorTracker* etArr[6];
RMSE* rmseT[6];
uint32_t cycleN = 333;
float rmsThreshold = 100;
float fros[4] = { 100.0 };
float Combinedfro = 0.0;

void initTrackers()
{
  for (int i = 0; i < 6; ++i)
  {
    etArr[i] = new ErrorTracker(bCoeffs, aCoeffs, order);
    rmseT[i] = new RMSE(cycleN);
  }
}
/////////////////////////

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
extern unsigned long _itcm_block_count[];
extern uint32_t external_psram_size;
extern char _ebss[], _heap_end[], *__brkval;
void memInfo()
{
  auto sp = (char*)__builtin_frame_address(0);
  logInfo("STACK: %7.2f KB / %4d KB (%6.2f%%)\n", (RAM_SIZE - (sp - _ebss)) / 1024.0, RAM_SIZE >> 10, 100.0 * (RAM_SIZE - (sp - _ebss)) / RAM_SIZE);
  logInfo("HEAP : %7.2f KB / %4d KB (%6.2f%%)\n", (RAM_SIZE - (_heap_end - __brkval)) / 1024.0, RAM_SIZE >> 10, 100.0 * (RAM_SIZE - (_heap_end - __brkval)) / RAM_SIZE);
}

float findMin(const float* arr, size_t len)
{
  float minVal = arr[0];
  for (size_t i = 1; i < len; ++i)
  {
    if (arr[i] < minVal) minVal = arr[i];
  }
  return minVal;
}

void sendIRQ()
{
  if (!(dataReceived && automatic))  // add armed or not check here.
    return;
  // if (modelFeedrate)

  manFeed.tock();
  fros[0] = manFeed.getFeedrate();
  fros[1] = 100;//findMin(axisFro, 6);
  fros[2] = 100; //findMin(modelFeedrate, 6);
  fros[3] = 100;//findMin(rmseAxis, 6);
  Combinedfro = findMin(fros, 4);
  frRemainder += ((uint8_t)(Combinedfro));
  uint32_t deltaIndex = floor(frRemainder / frMax);
  frRemainder %= frMax;
  ArrayIndex = (ArrayIndex + deltaIndex) % trajectoryLength;
  commandSent = true;
}

// float calcFROpos(float x)
// {
//   const float a = M_PI / 4;  // 45 degrees
//   const float b = M_PI / 3;  // 60 degrees
//   float absX = fabs(x);

//   if (absX <= a)
//     return 100.0;
//   else if (absX >= b)
//     return 0.0;
//   else
//     return 100.0 * (b - absX) / (b - a);
// }

inline float calcFROpos(float x)
{
  const float t1 = M_PI / 3.0, t2 = M_PI / 2.0;
  x = fabs(x);
  if (x < t1) return 100.0;
  if (x > t2) return 0.0;
  float a = (t2 - t1);
  float num = exp(a / (x - t2));
  float den = num + exp(a / (t1 - x));
  return 100.0 * num / den;
}
void cens(uint32_t n = 1)
{
  static unsigned long lastCall = 0;
  unsigned long now = millis();

  if (now - lastCall >= 1000 * n)
  {
    lastCall = now;
    memInfo();
  }
}

static inline int wrap_index(int idx, int size) {
    return ((idx % size) + size) % size;
}
#endif
