#include "FroCtrl.h"

IntervalTimer timer;
FeedrateGovernor governor(0, 10.0f, 100);
float tgtfr = 0.0;

volatile bool printFlag = false;
volatile unsigned int loopCounter = 0;
volatile float loopRateMHz = 0.0f;

void setup()
{
  Serial.begin(115200);
  while (!Serial)
    ;

  timer.begin(timerIRQ, 1000);  // 1 ms = 1 kHz
}

void loop()
{
  loopCounter++;

  if (printFlag)
  {
    printFlag = false;
    Serial.printf("%f,%f,%f,%f\n",
                  governor.getTarget(),
                  governor.getFeedrate(),
                  tgtfr,
                  loopRateMHz);
  }
}

void timerIRQ()
{
  governor.tick();
  loopRateMHz = loopCounter / 1000.0f;
  loopCounter = 0;
  printFlag = true;
}

void serialEvent()
{
  int bytesAvailable = Serial.available();
  if (Serial.available() < 1) return;
  char buffer[bytesAvailable + 1] = { 0 };

  int bytesRead = Serial.readBytes(buffer, bytesAvailable);
  buffer[bytesRead] = '\0';  // Null terminate

  String input(buffer);
  input.trim();

  float val = input.toFloat();
  if (val >= 0 && val <= 100)
  {
    tgtfr = val;
    governor.setTarget(val);
  }
}
