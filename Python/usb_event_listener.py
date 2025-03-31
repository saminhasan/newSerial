import win32gui
import win32con
import win32api
import threading
import win32gui_struct


class USBListener:
    """
    USB Listener Class to detect plug-in and removal of USB devices.
    Updates a provided callback function (e.g., Tkinter StringVar or custom handler).
    """

    def __init__(self, callback):
        """
        Initialize the USBListener.

        Args:
            callback (callable): A function or method that will be called with USB event messages.
                                 It should accept a single string argument.
        """
        self.callback = callback
        self.stop_event = threading.Event()
        self.hwnd = None  # Store window handle

    def _usb_event_handler(self, hwnd, msg, wparam, lparam):
        """Handles USB plug-in and removal events."""
        if msg == win32con.WM_DEVICECHANGE:
            if wparam == win32con.DBT_DEVICEARRIVAL:
                event_type = "USB Device Connected"
            elif wparam == win32con.DBT_DEVICEREMOVECOMPLETE:
                event_type = "USB Device Disconnected"
            else:
                event_type = f"Unknown USB Event: {wparam}"

            # Extract device information
            try:
                dev_broadcast = win32gui_struct.UnpackDEV_BROADCAST(lparam)
                device_name = getattr(dev_broadcast, "dbcc_name", "Unknown Device")
            except Exception as e:
                device_name = f"Error retrieving device info: {e}"

            message = f"{event_type} - Device: {device_name}"
            self.callback(message)
        return True

    def _listen(self):
        """Internal method to run the Windows message loop."""
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._usb_event_handler
        wc.lpszClassName = "USBListener"
        wc.hInstance = win32api.GetModuleHandle(None)
        class_atom = win32gui.RegisterClass(wc)
        self.hwnd = win32gui.CreateWindow(class_atom, "USB Listener", 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None)

        while not self.stop_event.is_set():
            win32gui.PumpWaitingMessages()

        win32gui.DestroyWindow(self.hwnd)
        win32gui.UnregisterClass(class_atom, wc.hInstance)

    def start(self):
        """Starts the USB listener in a separate thread."""
        self.stop_event.clear()
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()

    def stop(self):
        """Stops the USB listener."""
        self.stop_event.set()
        if self.hwnd:
            win32api.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
        self.listener_thread.join()


# Callback function to handle USB event messages
def handle_usb_event(message):
    # print(message)
    pass


if __name__ == "__main__":
    usb_listener = USBListener(callback=handle_usb_event)
    usb_listener.start()
    print("Listening for USB Connection Events")

    stop_event = threading.Event()
    import time

    try:
        # stop_event.wait()  # Wait indefinitely until an event is set
        time.sleep(1)
        raise "Stop Test"
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Stopping USB listener...")
        usb_listener.stop()
        stop_event.set()
    finally:
        print("Exiting cleanly.")
        exit(0)
