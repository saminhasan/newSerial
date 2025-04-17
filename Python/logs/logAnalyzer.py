import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import re
from datetime import datetime
from collections import defaultdict
import pandas as pd
import numpy as np

# Regex to match telemetry lines
error_pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+).*?\[INFO MSG\] T: (?P<tick>\d+), ID:(?P<id>\d+), u:(?P<u>[-\d.eE]+), y:(?P<y>[-\d.eE]+), AE: (?P<ae>[-\d.eE]+), PE: (?P<pe>[-\d.eE]+)'
)

# File picker
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Select log file", filetypes=[("Log Files", "*.log"), ("All Files", "*.*")])
if not file_path:
    print("No file selected.")
    exit()

# Parse data
data_by_id = defaultdict(lambda: {'ticks': [], 'ae': [], 'pe': [], 'u': [], 'y': []})

with open(file_path, 'r') as f:
    for line in f:
        match = error_pattern.search(line)
        if match:
            id_ = int(match.group("id"))
            tick = int(match.group("tick"))
            ae = float(match.group("ae"))
            pe = float(match.group("pe"))
            u = float(match.group("u"))
            y = float(match.group("y"))

            data_by_id[id_]['ticks'].append(tick)
            data_by_id[id_]['ae'].append(ae)
            data_by_id[id_]['pe'].append(pe)
            data_by_id[id_]['u'].append(u)
            data_by_id[id_]['y'].append(y)

# Check if data exists
if not data_by_id:
    print("No AE/PE telemetry data found.")
    exit()

# Sequential plots: one per ID
sorted_ids = sorted(data_by_id.keys())
# print(sorted_ids)
for id_ in sorted_ids:
    ticks = np.array(data_by_id[id_]['ticks'])
    ae = np.array(data_by_id[id_]['ae'])
    pe = np.array(data_by_id[id_]['pe'])

    time_s = (ticks - ticks[0]) / 1e6  # Convert from micros to seconds

    plt.figure(figsize=(10, 4))
    plt.plot(time_s, ae, label="AE", linewidth=2)
    plt.plot(time_s, pe, label="PE", linewidth=2, linestyle="--")
    plt.title(f"AE & PE for ID {id_}")
    plt.xlabel("Time (s)")
    plt.ylabel("Error")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    break

# # Export CSVs
for id_ in sorted_ids:
    ticks = np.array(data_by_id[id_]['ticks'])
    time_s = (ticks - ticks[0]) / 1e6  # Convert from micros to seconds

    df = pd.DataFrame({
        'time_s': time_s,
        'u': data_by_id[id_]['u'],
        'y': data_by_id[id_]['y'],
        'ae': data_by_id[id_]['ae'],
        'pe': data_by_id[id_]['pe'],
    })
    df.to_csv(f"id_{id_}_IMU.csv", index=False)
    break
