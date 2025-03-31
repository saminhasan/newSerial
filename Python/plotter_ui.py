import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
from collections import deque
import queue  # For queue.Empty
import numpy as np
from multiprocessing import Queue

class PlottingUI(ctk.CTkFrame):
    def __init__(self, parent, data_queue: Queue, max_rows=250):
        super().__init__(parent)
        self.data_queue = data_queue  # Shared multiprocessing queue
        self.max_rows = max_rows

        # Create a single-axis matplotlib figure.
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")

        self.x_data = deque(maxlen=max_rows)
        self.y_data = [deque(maxlen=max_rows) for _ in range(6)]
        
        self.lines = [self.ax.plot([], [], marker=".", ms=1, lw=1)[0] for _ in range(6)]
        
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        self.ax.set_title("Real-Time 6-Axis Plot")
        
        self.sample_index = 0
        
        self.after(1, self.update_plot)

    def update_plot(self):
        # Drain the queue; each message is expected to be an array of shape (N, 3).
        try:
            while True:
                batch = self.data_queue.get_nowait()
                batch = np.array(batch)
                for row in batch:
                    # Ensure exactly 3 values.
                    if len(row) != 3:
                        continue
                    # Duplicate the row:
                    # Axis 1 & 4 -> row[0], Axis 2 & 5 -> row[1], Axis 3 & 6 -> row[2]
                    duplicated = [row[0], row[1], row[2], row[0], row[1], row[2]]
                    
                    self.x_data.append(self.sample_index)
                    self.sample_index += 1

                    for i in range(6):
                        self.y_data[i].append(duplicated[i])
        except queue.Empty:
            pass

        # Update each line with the new data.
        for i in range(6):
            self.lines[i].set_data(self.x_data, self.y_data[i])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

        # Schedule the next update.
        self.after(10, self.update_plot)
