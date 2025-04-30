import numpy as np
import matplotlib.pyplot as plt

frequency_hz = 15.49193
deg = 4
output_file = f"sine{frequency_hz}Hz_{deg}D_1x.txt"
Ts = 1 / 1000 
T = 1 / frequency_hz
t = np.arange(0, T, Ts)
# y = np.radians(4) * np.sin(2 * np.pi * frequency_hz * t)
y = np.radians(deg) * np.sin(2 * np.pi * frequency_hz * t)

# # Trim last point if not circular
# if not np.isclose(y[0], y[-1], atol=1e-6):
#     y = y[:-1]

y = np.tile(y[:, None], (1, 6))  # Shape (N, 6)
cols_to_zero = [1,2,3,4,5]
y[:, cols_to_zero] = 0
# print(y[-2, :], y[-1, :], y[0, :], y[1, :], y[2, :])

np.savetxt(output_file, y, delimiter=",", fmt="%.9f")
print(output_file)
# Plot two periods (appended)
y_vis = np.concatenate([y[:, 0], y[:, 0]])
t_vis = np.arange(len(y_vis)) * Ts

plt.plot(t_vis, y_vis, '.-k')
plt.grid(True)
plt.show()
