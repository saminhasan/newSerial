#include <FroCtrl.h>

IntervalTimer timer;
FeedrateGovernor governor(0, 10.0f, 100);
float tgtfr = 0.0;

volatile bool printFlag = false;
volatile unsigned int loopCounter = 0;
volatile float loopRateMHz = 0.0f;
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

  // if (printFlag)
  // {
  //   printFlag = false;
  //   Serial.printf("%f,%f,%f,%f\n",
  //                 governor.getTarget(),
  //                 governor.getFeedrate(),
  //                 tgtfr,
  //                 loopRateMHz);
  // }
  cens();
}

void timerIRQ()
{
  governor.tock();
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

extern unsigned long _itcm_block_count[];
extern uint32_t external_psram_size;
extern char _ebss[], _heap_end[], *__brkval;
constexpr auto RAM_SIZE = 512 << 10;  // 512 KB
void memInfo()
{
  auto sp = (char *)__builtin_frame_address(0);
  Serial.printf("STACK: %7.2f KB / %4d KB (%6.2f%%)\n", (RAM_SIZE - (sp - _ebss)) / 1024.0, RAM_SIZE >> 10, 100.0 * (RAM_SIZE - (sp - _ebss)) / RAM_SIZE);
  Serial.printf("HEAP : %7.2f KB / %4d KB (%6.2f%%)\n", (RAM_SIZE - (_heap_end - __brkval)) / 1024.0, RAM_SIZE >> 10, 100.0 * (RAM_SIZE - (_heap_end - __brkval)) / RAM_SIZE);
}
