import customtkinter as ctk
from tooltip import CustomToolTip
from typing import Callable, Union

# _FONT = ("Cascadia Mono", 14)


class SpinboxSlider(ctk.CTkFrame):
    def __init__(
        self,
        *args,
        width: int = 200,
        height: int = 32,
        from_: float = 0,
        to: float = 200,
        step_size: Union[int, float] = 1,
        value: float = None,  # Initial value
        command: Callable[[float], None] = None,
        **kwargs,
    ):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.step_size = step_size
        self.command = command
        self.from_ = from_
        self.to = to
        self.value = value if value is not None else from_  # Set initial value

        self.configure(fg_color=("gray78", "gray28"))  # Frame color

        self.grid_columnconfigure(1, weight=1)  # Entry expands
        self.grid_rowconfigure(0, weight=1)  # Align widgets

        # Decrease Button
        self.subtract_button = ctk.CTkButton(
            self, text="-", width=height - 6, height=height - 6, command=self.decrease_value  # , font=_FONT
        )
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)

        # Entry (Spinbox)
        self.entry = ctk.CTkEntry(self, width=60, height=height - 6, border_width=0)  # , font=_FONT
        self.entry.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        self.entry.bind("<Return>", self.entry_event)
        self.entry.bind("<FocusOut>", self.entry_event)

        # Increase Button
        self.add_button = ctk.CTkButton(
            self, text="+", width=height - 6, height=height - 6, command=self.increase_value  # , font=_FONT
        )
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)

        # Slider
        self.slider = ctk.CTkSlider(
            self, from_=from_, to=to, number_of_steps=max(1, int((to - from_) / step_size)), command=self.slider_event
        )
        self.slider.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Tooltip for slider hover
        self.tooltip = CustomToolTip(self.slider, text=str(round(self.value)))

        self.slider.bind("<ButtonPress-1>", self.tooltip.show_tooltip)
        self.slider.bind("<ButtonRelease-1>", self.tooltip.hide_tooltip)
        self.set(self.value)  # Set initial value

    def update_value(self, value: float):
        """Updates both the entry, slider, tooltip, and calls the command callback."""
        self.value = max(self.from_, min(self.to, value))  # Clamp value
        self.entry.delete(0, "end")
        self.entry.insert(0, f"{int(self.value)}")
        self.slider.set(self.value)

        # Update tooltip
        self.update_tooltip_text()

        if self.command:
            self.command(self.value)

    def increase_value(self):
        """Increases the value by step_size."""
        try:
            value = float(self.entry.get()) + self.step_size
            self.update_value(value)
        except ValueError:
            pass

    def decrease_value(self):
        """Decreases the value by step_size."""
        try:
            value = float(self.entry.get()) - self.step_size
            self.update_value(value)
        except ValueError:
            pass

    def slider_event(self, value: float):
        """Triggered when the slider is moved."""
        self.update_value(value)

    def entry_event(self, event=None):
        """Triggered when the entry is modified."""
        try:
            value = float(self.entry.get())
            self.update_value(value)
        except ValueError:
            self.update_value(self.from_)

    def update_tooltip(self, event):
        """Update tooltip text and position when hovering over the slider."""
        if self.slider.winfo_width() > 0:
            hover_value = self.from_ + ((self.to - self.from_) * (event.x / self.slider.winfo_width()))
            hover_value = round(hover_value, 2)
            self.tooltip.update_text(str(round(hover_value)))

    def update_tooltip_text(self):
        """Update tooltip text and position on value change."""
        new_text = str(round(self.value))
        self.tooltip.update_text(new_text)

        if self.tooltip.tip_window:
            x, y = self.slider.winfo_pointerx(), self.slider.winfo_pointery()
            self.tooltip.tip_window.geometry(f"+{x+10}+{y-20}")

    def get(self) -> float:
        """Returns the current value."""
        return self.value

    def set(self, value: float):
        """Sets the value of both the entry and slider."""
        self.update_value(value)


# Example Usage
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  # Optional
    root = ctk.CTk()

    def on_value_change(value):
        print(f"Value changed: {value}")

    control = SpinboxSlider(root, from_=0, to=100, step_size=1, value=0, command=on_value_change)
    control.pack(padx=20, pady=20)

    root.mainloop()
