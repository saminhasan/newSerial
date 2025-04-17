#include "DMA_UART.h"
#include <Arduino.h>

#define IRQ_UART_PRIORITY  32  // 0 = highest priority, 255 = lowest
#define IRQ_DMA_PRIORITY  32  // 0 = highest priority, 255 = lowest

// define buffer sizes as 2^N with N at either 0,1,2,3,4,5,6 or 7 for buffer sizes of 1,2,4,8,16,32,64 or 128 elements
#define L2_RX_BUFSIZE 7 
#define L2_TX_BUFSIZE 7 

#define RX_BUFSIZE (1 << L2_RX_BUFSIZE)
#define TX_BUFSIZE (1 << L2_TX_BUFSIZE)
#define RX_BUFMASK (RX_BUFSIZE-1)
#define TX_BUFMASK (TX_BUFSIZE-1)

static DMAChannel RX8_dmachannel = DMAChannel();
static DMAChannel TX8_dmachannel = DMAChannel();

void DMA_Serial8_isr_dma()
{
  DMA_Serial8.isr_dma();
}

void DMA_Serial8_isr_uart()
{
  DMA_Serial8.isr_uart();
}

static uint16_t DMA_UART8_RxBuf[RX_BUFSIZE] __attribute__((aligned(RX_BUFSIZE*2)));  //receive buffer
static uint16_t DMA_UART8_TxBuf[TX_BUFSIZE] __attribute__((aligned(TX_BUFSIZE*2)));  //transmit buffer

static DMA_UART::hardware_t UART5_Hardware = {
	8, 5, IRQ_LPUART5, 
  &DMA_Serial8_isr_uart, 
  &DMA_Serial8_isr_dma, 
  CCM_CCGR3, CCM_CCGR3_LPUART5(CCM_CCGR_ON),
  {{34,1, &IOMUXC_LPUART5_RX_SELECT_INPUT, 1}, {48, 2, &IOMUXC_LPUART5_RX_SELECT_INPUT, 0}},
  {{35,1, &IOMUXC_LPUART5_TX_SELECT_INPUT, 1}, {0xff, 0xff, nullptr, 0}},
	IRQ_UART_PRIORITY, 
  IRQ_DMA_PRIORITY,
	XBARA1_OUT_LPUART5_TRG_INPUT
};

DMA_UART DMA_Serial8(&IMXRT_LPUART5, &UART5_Hardware, DMA_UART8_TxBuf, TX_BUFSIZE, TX_BUFMASK, DMA_UART8_RxBuf, RX_BUFSIZE, RX_BUFMASK, &TX8_dmachannel, &RX8_dmachannel);

#undef IRQ_UART_PRIORITY 
#undef IRQ_DMA_PRIORITY
#undef L2_RX_BUFSIZE 
#undef L2_TX_BUFSIZE
#undef RX_BUFSIZE
#undef TX_BUFSIZE
#undef RX_BUFMASK
#undef TX_BUFMASK
