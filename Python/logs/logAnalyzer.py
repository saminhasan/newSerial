import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import re
from datetime import datetime
from collections import defaultdict
import pandas as pd
import numpy as np

error_pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)'
    r'.*?\[INFO MSG\] T: (?P<tick>\d+), '
    r'ID:(?P<id>\d+), '
    r'u:(?P<u>[-\d.eE]+), '
    r'y:(?P<y>[-\d.eE]+), '
    r'CR: (?P<cr>[-\d.eE]+), '
    r'PE: (?P<pe>[-\d.eE]+), '
    r'RMSE: (?P<rmse>[-\d.eE]+)'
)

# File picker
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(
    title="Select log file",
    filetypes=[("Log Files", "*.log"), ("All Files", "*.*")]
)
print(file_path)
if not file_path:
    print("No file selected.")
    exit()

# Parse data,  including 'rmse'
data_by_id = defaultdict(lambda: {
    'ticks': [], 'cr': [], 'pe': [], 'u': [], 'y': [], 'rmse': []
})

with open(file_path, 'r') as f:
    for line in f:
        m = error_pattern.search(line)
        if not m:
            continue

        id_   = int(m.group("id"))
        tick  = int(m.group("tick"))
        u     = float(m.group("u"))
        y     = float(m.group("y"))
        cr    = float(m.group("cr"))
        pe    = float(m.group("pe"))
        rmse  = 0#float(m.group("rmse"))

        d = data_by_id[id_]
        d['ticks'].append(tick)
        d['u'].append(u)
        d['y'].append(y)
        d['cr'].append(cr)
        d['pe'].append(pe)
        d['rmse'].append(rmse)
if not data_by_id:
    print("No telemetry data found.")
    exit()

first_id = sorted(data_by_id.keys())[0]
d = data_by_id[first_id]
ticks = np.array(d['ticks'])
time_s = (ticks - ticks[0]) / 1e6

plt.figure(figsize=(10, 4))
plt.plot(time_s, d['cr'],   label="cr",   linewidth=2)
plt.plot(time_s, d['pe'],   label="PE",   linewidth=2, linestyle="--")
plt.plot(time_s, d['rmse'], label="RMSE", linewidth=1, linestyle=":")
plt.title(f"Errors & RMSE for ID {first_id}")
plt.xlabel("Time (s)")
plt.ylabel("Value")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Export CSVs (one per ID)
for id_, d in data_by_id.items():
    ticks = np.array(d['ticks'])
    time_s = (ticks - ticks[0]) / 1e6

    df = pd.DataFrame({
        'time_s': time_s,
        'u':      d['u'],
        'y':      d['y'],
        'cr':     d['cr'],
        'pe':     d['pe'],
        'rmse':   d['rmse'],
    })
    print(id_)
    df.to_csv(f"id_{id_}_IMU_PLT.csv", index=False)
    print("Saved")
    pass


# import tkinter as tk
# from tkinter import filedialog
# import matplotlib.pyplot as plt
# import re
# from datetime import datetime
# from collections import defaultdict
# import pandas as pd
# import numpy as np

# # Regex to match telemetry lines
# error_pattern = re.compile(
#     r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)'
#     r'.*?\[INFO MSG\] T: (?P<tick>\d+), '
#     r'ID:(?P<id>\d+), '
#     r'u:(?P<u>[-\d.eE]+), '
#     r'y:(?P<y>[-\d.eE]+), '
#     r'AE: (?P<ae>[-\d.eE]+), '
#     r'PE: (?P<pe>[-\d.eE]+), '
#     r'RMSE: (?P<rmse>[-\d.eE]+)'
# )

# # File picker
# root = tk.Tk()
# root.withdraw()
# file_path = filedialog.askopenfilename(title="Select log file", filetypes=[("Log Files", "*.log"), ("All Files", "*.*")])
# if not file_path:
#     print("No file selected.")
#     exit()

# # Parse data
# data_by_id = defaultdict(lambda: {'ticks': [], 'ae': [], 'pe': [], 'u': [], 'y': []})

# with open(file_path, 'r') as f:
#     for line in f:
#         match = error_pattern.search(line)
#         if match:
#             id_ = int(match.group("id"))
#             tick = int(match.group("tick"))
#             ae = float(match.group("ae"))
#             pe = float(match.group("pe"))
#             u = float(match.group("u"))
#             y = float(match.group("y"))

#             data_by_id[id_]['ticks'].append(tick)
#             data_by_id[id_]['ae'].append(ae)
#             data_by_id[id_]['pe'].append(pe)
#             data_by_id[id_]['u'].append(u)
#             data_by_id[id_]['y'].append(y)

# # Check if data exists
# if not data_by_id:
#     print("No AE/PE telemetry data found.")
#     exit()

# # Sequential plots: one per ID
# sorted_ids = sorted(data_by_id.keys())
# # print(sorted_ids)
# for id_ in sorted_ids:
#     ticks = np.array(data_by_id[id_]['ticks'])
#     ae = np.array(data_by_id[id_]['ae'])
#     pe = np.array(data_by_id[id_]['pe'])

#     time_s = (ticks - ticks[0]) / 1e6  # Convert from micros to seconds

#     plt.figure(figsize=(10, 4))
#     plt.plot(time_s, ae, label="AE", linewidth=2)
#     plt.plot(time_s, pe, label="PE", linewidth=2, linestyle="--")
#     plt.title(f"AE & PE for ID {id_}")
#     plt.xlabel("Time (s)")
#     plt.ylabel("Error")
#     plt.grid(True)
#     plt.legend()
#     plt.tight_layout()
#     plt.show()
#     break

# # # Export CSVs
# for id_ in sorted_ids:
#     ticks = np.array(data_by_id[id_]['ticks'])
#     time_s = (ticks - ticks[0]) / 1e6  # Convert from micros to seconds

#     df = pd.DataFrame({
#         'time_s': time_s,
#         'u': data_by_id[id_]['u'],
#         'y': data_by_id[id_]['y'],
#         'ae': data_by_id[id_]['ae'],
#         'pe': data_by_id[id_]['pe'],
#     })
#     # df.to_csv(f"id_{id_}_IMU_2.csv", index=False)
#     break