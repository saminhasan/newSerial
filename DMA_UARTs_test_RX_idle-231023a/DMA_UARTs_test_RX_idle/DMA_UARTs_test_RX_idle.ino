
#include "DMA_UART.h"

char test[20] = {'T', 'e', 's', 't', '!', 0};

void helptext ()
{
  Serial.printf ("DMA_Serial example for RX interrupt on idle.\nUsing Serial1 at 115200,n,8,1\nType 0,1,2 or 3 to trigger a test message out via TX1 pin\n");
}

void setup() 
{
  Serial.begin(115200);

  DMA_Serial1.begin (115200, SERIAL_8N1);
//  DMA_Serial1.begin_rx_interrupt_on_idle (4); 
  DMA_Serial1.begin_rx_interrupt_on_idle (4, idleActionFunction_Serial1);   // 4  -> 2^4 = 16 chars idle time for interrupt trigger, callback function is idleActionFunction() 

/*
  DMA_Serial2.begin ();
  DMA_Serial3.begin ();
  DMA_Serial4.begin ();
  DMA_Serial5.begin (115200, SERIAL_9N1, -1);
  DMA_Serial6.begin ();
  DMA_Serial7.begin ();
  DMA_Serial8.begin ();
*/

  helptext();
}  


char toASCII(char c)
{
  if (c < ' ') 
    c = ' ';
  return c;
}

const void idleActionFunction_Serial1 (void)
{
  int n;

  n = DMA_Serial1.available();

  Serial.printf("from Serial1 %d chars: ", n);  
  for (int i=0; i<n; i++)
  {
    char c = DMA_Serial1.read ();
    Serial.printf ("%02x='%c' ", c, toASCII(c));
  }
  Serial.printf("\n");  
}

void loop() 
{
/*
  int n;
  n = DMA_Serial1.available_after_nchars_idle();
  if (n)
    idleActionFunction();
*/


  if (Serial.available())
  {
    char st[100];

    char ch = Serial.read();
    switch (ch)
    {
      case '0': 
        DMA_Serial1.write (test);
        DMA_Serial1.trigger_tx ();
        break;
      case '1':
        sprintf (st, "01234\n"); 
        DMA_Serial1.write (st);
        DMA_Serial1.trigger_tx ();
        break;
      case '2':
        sprintf (st, "ABCdef"); 
        DMA_Serial1.write (st);
        DMA_Serial1.trigger_tx ();
        break;
      case '3':
        sprintf (st, "LONG\n"); 
        DMA_Serial1.write (st);
        DMA_Serial1.write (st);
        DMA_Serial1.write (st);
        DMA_Serial1.trigger_tx ();
        break;
      default:
        helptext();
        break;
    }
  }

}