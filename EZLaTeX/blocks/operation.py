import tkinter as tk
from tkinter import ttk, messagebox
from .base import Block, DISPLAY_FONT_SCALE, STANDARD_FONT_SIZES, MODAL_OFFSET

class OperationBlock(Block):
    def __init__(self, master, operation="+", font_size=10):
        self.operation = operation
        super().__init__(master, text=operation, font_size=font_size)

    def get_latex(self):
        op = r"\div" if self.operation=="÷" else self.operation
        return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont $\!\ {op}$}}"

    def edit(self, event):
        win = tk.Toplevel(self.master.winfo_toplevel())
        win.title("Edit Operation")
        win.geometry(f"+{self.widget.winfo_rootx()+MODAL_OFFSET}+{self.widget.winfo_rooty()+MODAL_OFFSET}")
        win.transient(self.master.winfo_toplevel()); win.grab_set()

        combo = ttk.Combobox(win, values=["+","-","x","=","÷"], width=5)
        combo.set(self.operation); combo.pack(pady=4)
        size_combo = ttk.Combobox(win, values=[str(s) for s in STANDARD_FONT_SIZES], width=5)
        size_combo.set(str(self.font_size)); size_combo.pack(pady=4)

        def save():
            try:
                size=int(size_combo.get())
            except ValueError:
                return messagebox.showerror("Invalid", "Enter integer font size.")
            self.font_size=min(STANDARD_FONT_SIZES, key=lambda s: abs(s-size))
            self.operation=combo.get().strip() or self.operation
            display=self.font_size if self.font_size<=16 else int(self.font_size*DISPLAY_FONT_SCALE)
            self.widget.config(text=self.operation, font=("Helvetica", display))
            win.destroy()

        tk.Button(win, text="Save", command=save).pack(pady=10)
        win.wait_window()
