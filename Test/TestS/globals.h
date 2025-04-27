#ifndef GLOBALS_H
#define GLOBALS_H

#define INPUT_BUFFER_SIZE 240016


#include <TeensyID.h>
#include <messages.h>
#include <motor_axis.h>
#include <packetParser.hpp>



uint8_t sysID;
uint8_t AXIS_L;
uint8_t AXIS_R;

const uint32_t ID1 = 15724840 ;//11304080
const uint32_t ID2 = 17015970;//17015970 
const uint32_t ID3 = 17016690;//17016690 
// const uint32_t ID1 = 15724840;
// const uint32_t ID2 = 17016000;
// const uint32_t ID3 = 17017360;

uint32_t teensySerialNumber = teensyUsbSN();

uint8_t USBBuffer[INPUT_BUFFER_SIZE];
PacketParser<usb_serial_class> parser(Serial, USBBuffer, INPUT_BUFFER_SIZE);
// void processPacket(const uint8_t* p, uint32_t packetLength);
//////////////////////////////////////////////
const int PROX_PIN1 = 38;  
const int PROX_INT2 = 2;
const int dir1 = -1;
const int dir2 = 1;
MotorAxis<FlexCAN_T4<CAN1, RX_SIZE_8, TX_SIZE_8>> motor1(0x01, PROX_PIN1, dir1, AXIS_L);
MotorAxis<FlexCAN_T4<CAN2, RX_SIZE_8, TX_SIZE_8>> motor2(0x01, PROX_INT2, dir2, AXIS_R);
IntervalTimer motor_timer;
bool automatic=false;
/////////////////////////////////////////////
extern unsigned long _itcm_block_count[];
extern uint32_t external_psram_size;
extern char _ebss[], _heap_end[], *__brkval;
void memInfo()
{
  auto sp = (char*)__builtin_frame_address(0);
  logInfo("STACK: %7.2f KB / %4d KB (%6.2f%%)\n", (RAM_SIZE - (sp - _ebss)) / 1024.0, RAM_SIZE >> 10, 100.0 * (RAM_SIZE - (sp - _ebss)) / RAM_SIZE);
  logInfo("HEAP : %7.2f KB / %4d KB (%6.2f%%)\n", (RAM_SIZE - (_heap_end - __brkval)) / 1024.0, RAM_SIZE >> 10, 100.0 * (RAM_SIZE - (_heap_end - __brkval)) / RAM_SIZE);
}
void cens(uint32_t n = 1)
{
  static unsigned long lastCall = 0;
  unsigned long now = millis();

  if (now - lastCall >= 1000 * n)
  {
    lastCall = now;
    // memInfo();
  }
}
#endif // GLOBALS_H
