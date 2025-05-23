import re
import gc
import os
import sys
import time
import serial
import logging
import numpy as np
from PIL import Image
from typing import Optional
import customtkinter as ctk
from messages import *
from itertools import batched
import multiprocessing as mp
from datetime import datetime
import serial.tools.list_ports
from tkinter import filedialog
import matplotlib.pyplot as plt
from multiprocessing import Queue
from spinbox import SpinboxSlider
from CTkMessagebox import CTkMessagebox
from usb_event_listener import USBListener
from binaryDecoder import parse_packets, logger_init

N = 60000
_FONT = ("Cascadia Mono", 14)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)
clear_icon = ctk.CTkImage(light_image=Image.open("clear-all-svgrepo-com.png"), size=(20, 20))

d_logger = logger_init()
def connect_to_serial(port: str, baudrate: int = 1000000, timeout: int = 1) -> Optional[serial.Serial]:
    """
    Attempts to connect to a serial port with error handling.

    Args:
        port (str): The serial port to connect to.
        baudrate (int, optional): The baud rate for the connection. Defaults to 480,000,000.
        timeout (int, optional): The timeout value in seconds. Defaults to 1.

    Returns:
        Optional[serial.Serial]: The serial connection object if successful, otherwise None.
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        if ser.is_open:
            print(f"Connected successfully to {port} at {baudrate} baud.")
            return ser
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {port}. {e}")
    except ValueError as e:
        print(f"Error: Invalid parameter value. {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None


def set_frame_state(frame, state="disabled"):
    """
    Enable or disable all widgets in a given frame.
    """
    for child in frame.winfo_children():
        try:
            child.configure(state=state)
        except Exception:
            pass


class SerialUIApp(ctk.CTkFrame):
    def __init__(self, parent, dq=None):
        super().__init__(parent)
        self.data_queue = dq  # Shared data queue for plotting.

        self.parent = parent
        self.connected = False
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self._create_main_frame()

        self.usb_listener = USBListener(callback=self.update_ports)
        self.usb_listener.start()
        self.update_ports()

        # Bind Escape key to clear widget focus.
        def clear_focus(event=None):
            parent.focus_set()

        self.parent.bind("<Escape>", clear_focus)

        self.serial_process = None
        self.serial_rx_queue = None
        self.serial_tx_queue = None

        self.update_output_textbox()

    def _create_control_panel_frame(self):
        self.arm_state = False
        self.mode_state: bool = False
        self.speed: int = 0
        """Right-side control panel."""
        self.control_panel = ctk.CTkFrame(self)
        self.control_panel.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=5, pady=5)

        self.sendPoseBtn = ctk.CTkButton(self.control_panel, text="Send Pose", command=self.send_data_array)
        self.sendPoseBtn.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.arm_button = ctk.CTkButton(self.control_panel, text="Arm", command=self.toggle_arm_state)
        self.arm_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.calibrate_button = ctk.CTkButton(self.control_panel, text="Calibrate", command=self.calibrate)
        self.calibrate_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.position_entry = ctk.CTkEntry(self.control_panel, placeholder_text="")
        self.position_entry.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.position_entry.bind("<Return>", lambda event: self.send_position())

        self.send_pos_button = ctk.CTkButton(self.control_panel, text="Send Pos", command=self.send_position)
        self.send_pos_button.grid(row=2, column=1, padx=5, pady=5, sticky="ew")



        self.StagePose = ctk.CTkButton(self.control_panel, text=f"InitPos", command=self.InitPose)
        self.StagePose.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.mode_select = ctk.CTkButton(self.control_panel, text=f"automatic", command=self.toggle_mode)
        self.mode_select.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.feedRateLbl = ctk.CTkLabel(self.control_panel, text="Feedrate", height=18)
        self.feedRateLbl.grid(row=6, column=0, columnspan=2, padx=5, sticky="ew")
        self.spinbox = SpinboxSlider(self.control_panel, to=100, step_size=1, value=self.speed)
        self.spinbox.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.spinbox.command = self.slider_event
        self.eStop_button = ctk.CTkButton(self.control_panel, text="eStop",  fg_color="red4", hover_color="red", command=self.send_eStop)
        self.eStop_button.grid(row=8, column=0, columnspan=2, rowspan=2,padx=5, pady=5, sticky="nsew")
        self.control_panel.grid_rowconfigure(8,weight=1)
        self.reboot_button = ctk.CTkButton(
            self.control_panel, text=f"Reboot", command=self.send_reboot_command, fg_color="red4", hover_color="red"
        )
        self.reboot_button.grid(row=10, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

    def _create_main_frame(self):
        """Main frame with connection settings, log output, and input area."""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=10, pady=0)
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=3)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._create_connection_frame()
        self._create_log_output()
        self._create_input_section()
        self._create_control_panel_frame()

    def _create_connection_frame(self):
        """Top frame with COM port selection and connect button."""
        connection_frame = ctk.CTkFrame(self.main_frame, corner_radius=0)
        connection_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        self.com_label = ctk.CTkLabel(connection_frame, text="COM Port:")
        self.com_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.selected_port = ctk.StringVar(value="Select Port")
        self.port_details = []
        self.port_menu = ctk.CTkOptionMenu(
            connection_frame,
            variable=self.selected_port,
            values=self.port_details,
            command=self.update_selected_port,
            font=_FONT,
        )
        self.port_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.device_filter = ctk.BooleanVar(value=True)
        self.teensy_only_checkbox = ctk.CTkCheckBox(
            connection_frame, text="Teensy only", variable=self.device_filter, command=self.update_ports
        )
        self.teensy_only_checkbox.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.connect_button = ctk.CTkButton(connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    def _create_log_output(self):
        """Log output textbox."""
        self.output_textbox = ctk.CTkTextbox(self.main_frame, corner_radius=0, wrap=ctk.NONE)
        self.output_textbox.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.output_textbox.tag_config("red", foreground="red")
        self.output_textbox.tag_config("green", foreground="green")

    def _create_input_section(self):
        """Input area with a text entry, send button, and clear (X) button."""
        input_frame = ctk.CTkFrame(self.main_frame, corner_radius=0)
        input_frame.grid(row=2, column=0, padx=0, pady=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=4)
        input_frame.grid_columnconfigure(1, weight=0)
        input_frame.grid_columnconfigure(2, weight=0)

        self.input_textbox = ctk.CTkEntry(input_frame)
        self.input_textbox.grid(row=0, column=0, padx=0, pady=5, sticky="ew")
        self.input_textbox.bind("<Return>", lambda event: self.send_text())

        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.send_text, height=32)
        self.send_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        self.clear_button = ctk.CTkButton(
            input_frame,
            text="",
            image=clear_icon,
            width=32,
            height=32,
            command=self.clear_output_textbox,
            fg_color="#2b2b2b",
            hover_color="#646464",
        )
        self.clear_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.clear_button.configure(state="normal")

    def update_ports(self, msg=None):
        """
        Refresh the list of available COM ports.
        If the connected device is removed, disconnect.
        """
        ports = serial.tools.list_ports.comports()
        if self.connected:
            print("Connected USB device removed. Disconnecting...")
            self.disconnect_serial()
            # print("Raise Popup")
            CTkMessagebox(
                title="Error",
                message="Something went wrong!!!",
                icon="cancel",
                sound=True,
            )
        if self.device_filter.get():
            teensy_ports = [port for port in ports if port.vid == 5824 and port.pid in [0x0483]]
            self.port_details = [f"{port.device} - {port.description}" for port in teensy_ports] or ["No Teensy devices found"]
        else:
            self.port_details = [f"{port.device} - {port.description}" for port in ports] or ["No COM ports available"]

        self.port_menu.configure(values=self.port_details)
        if self.port_details and "No" not in self.port_details[0]:
            self.selected_port.set(self.port_details[0].split()[0])
        else:
            self.selected_port.set("Select Port")

    def update_selected_port(self, selected_detail):
        """Update the selected port from the dropdown."""
        self.selected_port.set(selected_detail.split()[0])

    def toggle_connection(self):
        """Connect or disconnect the serial device."""
        if self.connected:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        """
        Open the serial connection by starting a dedicated process that handles I/O.
        Here we only pass the port string so that the child process creates its own connection.
        """
        port = self.selected_port.get()
        if port == "Select Port" or not port:
            print("No valid COM port selected.")
            return

        self.connected = True
        self.connect_button.configure(text="Disconnect")
        self.send_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        set_frame_state(self.control_panel, "normal")
        # Create RX and TX queues.
        self.serial_rx_queue = mp.Queue(maxsize=536870912)
        self.serial_tx_queue = mp.Queue(maxsize=536870912)
        self.serial_process = mp.Process(
            target=self.serial_comm_process,
            args=(port, self.serial_rx_queue, self.serial_tx_queue), # add status queue here to popup for a unsuccessful connection.
            name="MyCustomProcessName",
        )
        self.serial_process.start()
        self.com_label.configure(state="disabled")
        self.port_menu.configure(state="disabled")
        self.teensy_only_checkbox.configure(state="disabled")

    def disconnect_serial(self):
        """Disconnect serial and stop the reader process."""
        if self.connected:
            self.connect_button.configure(text="Connect")
            self.connected = False
            print("Disconnected.")

            if self.serial_process and self.serial_process.is_alive():
                self.serial_process. kill()
                self.serial_process.join()
        else:
            print("No active connection to disconnect.")
        self.com_label.configure(state="normal")
        self.port_menu.configure(state="normal")
        self.teensy_only_checkbox.configure(state="normal")

    @staticmethod
    def serial_comm_process(port: str, rx_queue: "Queue[str]", tx_queue: "Queue[bytes]") -> None:
        """
        Process that handles both reading from and writing to the serial port.
        The child process opens its own connection using the provided port.

        Args:
            port (str): The serial port to connect to.
            rx_queue (Queue[str]): A queue for receiving data from the serial port.
            tx_queue (Queue[bytes]): A queue for sending data to the serial port.
        """
        # time_string = datetime.now().replace(microsecond=0).isoformat().replace(":", "-")  # Consistent timestamp
        # print(time_string)
        # log_dir = "logs"
        # os.makedirs(log_dir, exist_ok=True)
        # log_filename = f"log_{time_string}.log"
        # log_file = os.path.join(log_dir, log_filename)

        # logging.basicConfig(
        #     level=logging.INFO,
        #     format="%(asctime)s - %(levelname)s - %(message)s",
        #     handlers=[
        #         logging.FileHandler(log_file, mode="w"),  # Create a new log file each time
        #         # logging.StreamHandler()  # Print logs to console as well
        #     ],
        # )

        # logger = logging.getLogger("SerialLogger")
        # logger.info("Logger started.")
        input_buffer = b""
        ser = connect_to_serial(port=port)
        if ser is None:
            print("Child process: Unable to open serial connection.") # pop up
            # logger.info("Child process: Unable to open serial connection.")
            return
        try:
            while True:
                if ser.out_waiting == 0:
                    queue_size = tx_queue.qsize()  # Get number of items to process
                    if queue_size > 0:
                        for _ in range(queue_size):
                            outgoing_data = tx_queue.get()
                            ser.write(outgoing_data)
                if ser.in_waiting > 0:
                    input_buffer += ser.read(ser.in_waiting)
                input_buffer = parse_packets(input_buffer, rx_queue, d_logger)
                time.sleep(5e-4)
        except Exception as e:
            print(f"Serial process error: {e}")
            # logger.info(f"Serial process error: {e}")  # Log received data as text

    def update_output_textbox(self, data=None) -> None:
        """Fetch data from the RX queue and update the UI textbox efficiently."""
        if data is None:
            data_list = []
            if self.serial_rx_queue:
                queue_size = self.serial_rx_queue.qsize()
                if queue_size > 0:
                    data_list = [self.serial_rx_queue.get() for _ in range(queue_size)]

            if data_list:
                data = "".join(data_list)

            else:
                data = None

        if data:
            self.insert_text_with_highlight(data)
            self.output_textbox.yview("end")
            # add dq handler here
        num_lines = int(self.output_textbox.index("end-1c").split(".")[0])
        max_lines = 5000
        if num_lines > max_lines:
            self.output_textbox.delete("1.0", f"{num_lines - max_lines}.0")
        self.after(20, self.update_output_textbox)

    def send_text(self) -> None:
        text :str = self.input_textbox.get() + "\n"
        self.input_textbox.delete(0, "end")
        text_cmd = Info(sysID=np.uint8(0),value=text)
        data = text_cmd.rawBytes
        print(f"Sent: {data}")  
        if self.connected:
            self.serial_tx_queue.put(data)
    def toggle_arm_state(self) -> None:
        """Toggle between armed and disarmed states."""
        self.arm_state = not self.arm_state
        self.arm_button.configure(text="Arm" if not self.arm_state else "Disarm")
        if self.arm_state:
            arm_cmd = Enable()
            data = arm_cmd.rawBytes
            if self.connected:
                self.serial_tx_queue.put(data)
        else:
            disarm_cmd = Disable()
            data = disarm_cmd.rawBytes
            if self.connected:
                self.serial_tx_queue.put(data)
    def calibrate(self) -> None:
        """Send a calibration command."""
        calibrate_cmd = Calibrate()
        data = calibrate_cmd.rawBytes
        if self.connected:
            self.serial_tx_queue.put(data)

    def send_position(self, position=0) -> None:
        """Send position data from the position entry field safely."""
        pos = self.position_entry.get() or "0"
        try:
            pos = np.radians(float(pos))
        except ValueError:
            print("Error: Invalid position input.")
            return
        pos_cmd = pose6D(value=np.full((1, 6), pos, dtype=np.float32))
        data = pos_cmd.rawBytes
        if self.connected:
            self.serial_tx_queue.put(data)
        self.position_entry.delete(0, "end")

    def send_data_array(self) -> None:
        """
        Open a file dialog to select a control signal file.
        Load, plot the data, and start sending it non-blockingly.
        """
        file_path = filedialog.askopenfilename(
            title="Select a Control Signal File",
            filetypes=[
                ("Text Files", "*.txt"),
                ("CSV Files", "*.csv"),
                ("All Files", "*.*"),
            ],
        )
        if file_path:
            print(f"Selected file: {file_path}")
            try:
                data = np.loadtxt(file_path, delimiter=",", dtype=np.float32)
                n = data.shape[0]
                signal = data
                print(signal[0:5,:])
                self.speed = 0
                self.spinbox.update_value(self.speed)
                ## set to manual mode, low gains.
                self.mode_state = False
                self.mode_select.configure(text=f"{"automatic" if not self.mode_state else "manual"}")
                mode_cmd = Mode(value=np.uint8(0x00))
                if self.connected:
                    self.serial_tx_queue.put(mode_cmd.rawBytes)
                trajectory_length = TrajectoryLength(value=np.uint32(n))
                if self.connected:
                    self.serial_tx_queue.put(trajectory_length.rawBytes)

                trajectory = Trajectory6D( value=signal.astype(np.float32))
                if self.connected:
                    trajectory_packed = trajectory.rawBytes
                    self.serial_tx_queue.put(trajectory_packed)

            except Exception as e:
                print(f"Error loading file: {e}")



    def InitPose(self):
        stage_cmd = stagePosition()
        if self.connected:
            self.serial_tx_queue.put(stage_cmd.rawBytes)

    def toggle_mode(self) -> None:
        """Toggle between manual and auto mode."""
        self.mode_state = not self.mode_state
        self.mode_select.configure(text=f"{"automatic" if not self.mode_state else "manual"}")
        # print(f"Mode : {np.uint8(0x01) if self.mode_state else np.uint8(0x00)}")
        mode_cmd = Mode(value=np.uint8(0x01) if self.mode_state else np.uint8(0x00))
        if self.connected:
            self.serial_tx_queue.put(mode_cmd.rawBytes)

    def slider_event(self, value=0) -> None:
        self.speed = value
        # print(f"speed: {value}")
        feedrate_cmd = FeedRate(value=np.uint8(value))
        if self.connected:
            self.serial_tx_queue.put(feedrate_cmd.rawBytes)
    def send_eStop(self):
        if self.connected:
            self.serial_tx_queue.put(eStop().rawBytes)
        feedrate_cmd = FeedRate(value=np.uint8(0))
        if self.connected:
            self.serial_tx_queue.put(feedrate_cmd.rawBytes)
        self.after(100, self.disarm)

    def disarm(self):
        print("DISARMED ESTOP")
        disarm_cmd = Disable()
        data = disarm_cmd.rawBytes
        if self.connected:
            self.serial_tx_queue.put(data)
    def send_reboot_command(self) -> None:
        if self.connected:
            self.serial_tx_queue.put(Reboot().rawBytes)

    def clear_output_textbox(self) -> None:
        """Clear the log output textbox."""
        self.output_textbox.delete("1.0", "end")

    def quit_app(self) -> None:
        """
        Cleanly quit the application:
        - Disconnect any active serial connection.
        - Stop the USB listener.
        - Quit the main loop.
        """
        self.parent.quit()
        self.usb_listener.stop()
        if self.arm_state:
            print("Disarming before quit...")
        print("Quitting application...")
        if self.connected:
            self.disconnect_serial()
        # # get yes/no answers
        # msg = CTkMessagebox(
        #     title="Exit?",
        #     message="Do you want to close the program?",
        #     icon="question",
        #     option_1="Cancel",
        #     option_2="No",
        #     option_3="Yes",
        #     header=False,
        # )
        # response = msg.get()

        # if response == "Yes":
        #     self.parent.quit()
        #     self.usb_listener.stop()
        #     if self.arm_state:
        #         print("Disarming before quit...")
        #     print("Quitting application...")
        #     if self.connected:
        #         self.disconnect_serial()
        # else:
        #     return

    def insert_text_with_highlight(self, text):
        """Inserts text into the textbox and highlights 'LoopRate' occurrences."""
        # Get current end position before inserting text
        current_end = self.output_textbox.index("end-1c")  # Get last line before insert
        last_line_number = int(current_end.split('.')[0])  # Extract last line number

        # Insert new text at the end
        self.output_textbox.insert("end", text + '\n')

        # Regex pattern to match "LoopRate: X.XX [unit]"
        # pattern = r"LoopRate:\s*\d+\.\d+\s*(?:Hz|KHz|MHz)"
        pattern = r"LoopRate:\s*\d+(?:\.\d+)?\s*(?:Hz|KHz|MHz)"


        # Find occurrences in the newly added text
        lines = text.split("\n")
        for line_offset, line in enumerate(lines):
            for match in re.finditer(pattern, line):
                # Compute correct line index in the textbox
                start_line = last_line_number + line_offset  # Adjust line number
                start_index = f"{start_line}.{match.start()}"
                end_index = f"{start_line}.{match.end()}"

                # Apply the highlight tag
                self.output_textbox.tag_add("red", start_index, end_index)

if __name__ == "__main__":
    data_queue = mp.Queue()

    # For Windows support.
    # mp.freeze_support()
    root = ctk.CTk()
    # root.option_add("*Font", _FONT)
    root.title("Serial Monitor with Tab View")
    app = SerialUIApp(root, data_queue)
    app.pack(expand=True, fill="both")
    root.update_idletasks()
    width = root.winfo_reqwidth() + 480
    height = root.winfo_reqheight() + 240
    root.geometry(f"{width}x{height}")
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()
