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

static DMAChannel RX4_dmachannel = DMAChannel();
static DMAChannel TX4_dmachannel = DMAChannel();

void DMA_Serial4_isr_dma()
{
  DMA_Serial4.isr_dma();
}

void DMA_Serial4_isr_uart()
{
  DMA_Serial4.isr_uart();
}

static uint16_t DMA_UART4_RxBuf[RX_BUFSIZE] __attribute__((aligned(RX_BUFSIZE*2)));  //receive buffer
static uint16_t DMA_UART4_TxBuf[TX_BUFSIZE] __attribute__((aligned(TX_BUFSIZE*2)));  //transmit buffer

static DMA_UART::hardware_t UART3_Hardware = {
	4, 3, IRQ_LPUART3, 
  &DMA_Serial4_isr_uart, 
  &DMA_Serial4_isr_dma, 
  CCM_CCGR0, CCM_CCGR0_LPUART3(CCM_CCGR_ON),
  {{16,2, &IOMUXC_LPUART3_RX_SELECT_INPUT, 0}, {0xff, 0xff, nullptr, 0}},
  {{17,2, &IOMUXC_LPUART3_TX_SELECT_INPUT, 0}, {0xff, 0xff, nullptr, 0}},
	IRQ_UART_PRIORITY, 
  IRQ_DMA_PRIORITY,
	XBARA1_OUT_LPUART3_TRG_INPUT
};

DMA_UART DMA_Serial4(&IMXRT_LPUART3, &UART3_Hardware, DMA_UART4_TxBuf, TX_BUFSIZE, TX_BUFMASK, DMA_UART4_RxBuf, RX_BUFSIZE, RX_BUFMASK, &TX4_dmachannel, &RX4_dmachannel);

#undef IRQ_UART_PRIORITY 
#undef IRQ_DMA_PRIORITY
#undef L2_RX_BUFSIZE 
#undef L2_TX_BUFSIZE
#undef RX_BUFSIZE
#undef TX_BUFSIZE
#undef RX_BUFMASK
#undef TX_BUFMASK
