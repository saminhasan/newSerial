import os
import time
import serial
import logging
from datetime import datetime
from multiprocessing import Process, Queue
from messages import *
import os
import time
import serial
import logging
from datetime import datetime
from multiprocessing import Process, Queue
from messages import *
from threading import Thread
class SerialCommHandler:
    def __init__(self, port: str, rx_queue: "Queue[bytes]", tx_queue: "Queue[bytes]"):
        self.port = port
        self.rx_queue = rx_queue
        self.tx_queue = tx_queue
        self.teensy = None
        self.logger = self._setup_logger()
        self.logger.info(f"<Ready>")

    def _setup_logger(self):
        time_string = datetime.now().replace(microsecond=0).isoformat().replace(":", "-")
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"log_{time_string}.log")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, mode="w"),
                logging.StreamHandler()
            ],
        )
        return logging.getLogger("SerialLogger")


    def _open_port(self):
        self.logger.info(f"<_open_port>")
        if self.teensy is not None and self.teensy.is_open:
            try:
                self.teensy.close()
            except Exception:
                pass
        self.teensy = serial.Serial(self.port, timeout=0)
        self.logger.info(f"DONE : <_open_port>")

    def _close_port(self):
        self.logger.info(f"<_close_port>")
        if self.teensy is not None:
            try:
                if self.teensy.is_open:
                    self.teensy.close()
                self.logger.info("Serial port closed.")
            except Exception as e:
                self.logger.warning(f"Error closing port: {e}")
            finally:
                self.teensy = None
        self.logger.info(f"DONE : <_close_port>")

    def _handle_tx(self):
            if self.teensy.out_waiting == 0:
                queue_size = self.tx_queue.qsize()
                if queue_size > 0:
                    for _ in range(queue_size):
                        outgoing_data = self.tx_queue.get()
                        self.teensy.write(outgoing_data)
                        self.logger.info(f"TX (Hex): {outgoing_data.hex()}")

    def _handle_rx(self):
        if self.teensy.in_waiting > 0:
            incoming = self.teensy.read(self.teensy.in_waiting)
            self.rx_queue.put(incoming)
            self.logger.info(f"RX (Hex): {incoming.hex()}")

    def run(self):
        """Entry point for Process target."""
        self.logger.info("Serial communication process started.")
        self._connect_and_run()

    def _connect_and_run(self):
        try:
            self._open_port()
            with self.teensy:
                self.logger.info(f"Opened serial port: {self.port}")
                while True:
                    self._handle_tx()
                    self._handle_rx()
                    time.sleep(5e-4)
        except Exception as e:
            self.logger.warning(f"Serial error: {e}")
        finally:
            self._close_port()
            time.sleep(2)
            self._connect_and_run()

if __name__ == '__main__':
    serial_rx_queue = Queue(maxsize=2**20)
    serial_tx_queue = Queue(maxsize=2**20)

    handler = SerialCommHandler("COM6", serial_rx_queue, serial_tx_queue)
    serial_process = Thread(target=handler.run)
    serial_process.start()

    for msg in test_cases:
        serial_tx_queue.put(msg.rawBytes)
        time.sleep(1)
        print(serial_rx_queue.get())

