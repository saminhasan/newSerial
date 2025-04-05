import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import re
from datetime import datetime
from collections import defaultdict

# Regex to match ID-based AE/PE logs
error_pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+).*?\[INFO MSG\] ID:(?P<id>\d+), AE: (?P<ae>[-\d.eE]+), PE: (?P<pe>[-\d.eE]+)'
)

# File picker
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Select log file", filetypes=[("Log Files", "*.log"), ("All Files", "*.*")])
if not file_path:
    print("No file selected.")
    exit()

# Parse data
data_by_id = defaultdict(lambda: {'timestamps': [], 'ae': [], 'pe': []})

with open(file_path, 'r') as f:
    for line in f:
        match = error_pattern.search(line)
        if match:
            ts = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S,%f")
            id_ = int(match.group("id"))
            ae = float(match.group("ae"))
            pe = float(match.group("pe"))

            data_by_id[id_]['timestamps'].append(ts)
            data_by_id[id_]['ae'].append(ae)
            data_by_id[id_]['pe'].append(pe)

# Check if data exists
if not data_by_id:
    print("No AE/PE data found.")
    exit()

# Sequential plots: one per ID
sorted_ids = sorted(data_by_id.keys())

for id_ in sorted_ids:
    ts = data_by_id[id_]['timestamps']
    ae = data_by_id[id_]['ae']
    pe = data_by_id[id_]['pe']

    plt.figure(figsize=(10, 4))
    plt.plot(ts, ae, label="AE", linewidth=2)
    plt.plot(ts, pe, label="PE", linewidth=2, linestyle="--")
    plt.title(f"AE & PE for ID {id_}")
    plt.xlabel("Time")
    plt.ylabel("Error")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.gcf().autofmt_xdate()
    plt.show()  # blocks
