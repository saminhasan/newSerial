# import customtkinter as ctk
# import multiprocessing as mp
# import queue
# from ui_main import SerialUIApp
# from optimized_plotter import PlottingUI  # Import the new PyQtGraph-based PlottingUI
# from pyqtgraph.Qt import QtWidgets
# import sys

# def switch_theme():
#     current_mode = ctk.get_appearance_mode()
#     ctk.set_appearance_mode("Dark" if current_mode == "Light" else "Light")

# if __name__ == "__main__":
#     mp.freeze_support()
#     WIDTH, HEIGHT = 1000, 800
#     ctk.set_appearance_mode("System")
#     root = ctk.CTk()
#     root.title("Tabbed Window with Theme Switch")
#     root.geometry(f"{WIDTH}x{HEIGHT}")
#     root.minsize(WIDTH, HEIGHT)

#     # Create a tab view
#     tab_view = ctk.CTkTabview(root)
#     tab_view.pack(expand=True, fill="both", padx=20, pady=0, anchor="center")

#     # Create tabs
#     tab1 = tab_view.add("                  Connection                  ")
#     tab2 = tab_view.add("                    Control                   ")
#     tab3 = tab_view.add("                  Tab 3                  ")

#     # Shared queue between SerialUIApp and PlottingUI
#     data_queue = queue.Queue()

#     # Embed SerialUIApp in tab1
#     serial_ui_frame = SerialUIApp(tab1, data_queue)
#     serial_ui_frame.pack(expand=True, fill="both")

#     # Embed PyQtGraph-based PlottingUI in tab2
#     plot_frame = PlottingUI(tab2, data_queue)
#     plot_frame.pack(expand=True, fill="both")

#     # Populate tab3 with widgets
#     label3 = ctk.CTkLabel(tab3, text="This is Tab 3")
#     label3.pack(pady=10)

#     # Add a button to switch themes
#     theme_button = ctk.CTkButton(root, text="Switch Theme", command=switch_theme)
#     theme_button.pack(pady=10)

#     root.protocol("WM_DELETE_WINDOW", serial_ui_frame.quit_app)
#     root.mainloop()








import customtkinter as ctk
import multiprocessing as mp
from ui_main import SerialUIApp
from plotter_ui import PlottingUI  # Assuming PlottingUI is in plot_tab.py

def switch_theme():
    current_mode = ctk.get_appearance_mode()
    ctk.set_appearance_mode("Dark" if current_mode == "Light" else "Light")

if __name__ == "__main__":
    mp.freeze_support()
    WIDTH, HEIGHT = 1000, 800
    ctk.set_appearance_mode("System")
    root = ctk.CTk()
    root.title("Tabbed Window with Theme Switch")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    root.minsize(WIDTH, HEIGHT)

    # Create a tab view
    tab_view = ctk.CTkTabview(root)
    tab_view.pack(expand=True, fill="both", padx=20, pady=0, anchor="center")

    # Create tabs
    tab1 = tab_view.add("                  Connection                  ")
    tab2 = tab_view.add("                    Control                   ")
    tab3 = tab_view.add("                  Tab 3                  ")

    # Shared queue between SerialUIApp and PlottingUI
    data_queue = mp.Queue()

    # Embed SerialUIApp in tab1
    serial_ui_frame = SerialUIApp(tab1, data_queue)
    serial_ui_frame.pack(expand=True, fill="both")

    # Embed PlottingUI in tab2
    plot_frame = PlottingUI(tab2, data_queue)
    plot_frame.pack(expand=True, fill="both")

    # Populate tab3 with widgets
    label3 = ctk.CTkLabel(tab3, text="This is Tab 3")
    label3.pack(pady=10)

    # Add a button to switch themes
    theme_button = ctk.CTkButton(root, text="Switch Theme", command=switch_theme)
    theme_button.pack(pady=10)

    root.protocol("WM_DELETE_WINDOW", serial_ui_frame.quit_app)

    root.mainloop()
