import customtkinter as ctk

# _FONT = ("Cascadia Mono", 14)


class CustomToolTip:
    def __init__(self, widget, text="", bg_color="black", fg_color="white", corner_radius=10, delay=0):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.corner_radius = corner_radius
        self.delay = delay  # Delay in milliseconds (1000 ms = 1 sec)
        self.hover_id = None

        self.widget.bind("<Motion>", self.update_tooltip)

    def show_tooltip(self, event=None):
        if self.tip_window:
            return
        # x, y = self.widget.winfo_rootx() + 25, self.widget.winfo_rooty() - 10
        x, y = self.widget.winfo_pointerx(), self.widget.winfo_pointery()

        self.tip_window = ctk.CTkToplevel(self.widget)
        self.tip_window.overrideredirect(True)
        self.tip_window.geometry(f"+{x}+{y}")

        self.label = ctk.CTkLabel(
            self.tip_window,
            text=self.text,
            # fg_color=self.bg_color,
            text_color=self.fg_color,
            corner_radius=self.corner_radius,
            padx=10,
            pady=5,
            # font=_FONT,
        )
        self.label.pack()

    def update_tooltip(self, event):
        if self.tip_window:
            x, y = event.x_root + 10, event.y_root - 20
            self.tip_window.geometry(f"+{x}+{y}")

    def hide_tooltip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    def update_text(self, text):
        if self.tip_window:
            self.label.configure(text=text)
        self.text = text
