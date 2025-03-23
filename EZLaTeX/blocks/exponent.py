import tkinter as tk
from tkinter import ttk, messagebox
from .base import Block, DISPLAY_FONT_SCALE, STANDARD_FONT_SIZES, MODAL_OFFSET

class ExponentBlock(Block):
    def __init__(self, master, base="x", exponent="2", font_size=10):
        self.base, self.exponent = base, exponent
        super().__init__(master, text=f"{base}^{exponent}", font_size=font_size)

    def get_latex(self):
        return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont $\!\ {self.base}^{{{self.exponent}}}$}}"

    def update_display(self):
        display = self.font_size if self.font_size <= 16 else int(self.font_size * DISPLAY_FONT_SCALE)
        self.widget.config(text=f"{self.base}^{self.exponent}", font=("Helvetica", display))

    def delete_and_close(self, win):
        self.master.editor.delete_block(self)
        win.destroy()

    def edit(self, event):
        win = tk.Toplevel(self.master.winfo_toplevel())
        win.title("Edit Exponent")
        win.geometry(f"+{self.widget.winfo_rootx()+MODAL_OFFSET}+{self.widget.winfo_rooty()+MODAL_OFFSET}")
        win.transient(self.master.winfo_toplevel())
        win.grab_set()

        tk.Label(win, text="Base:").pack(pady=4)
        base_var = tk.StringVar(value=self.base)
        tk.Entry(win, textvariable=base_var).pack(pady=4)

        tk.Label(win, text="Exponent:").pack(pady=4)
        exp_var = tk.StringVar(value=self.exponent)
        tk.Entry(win, textvariable=exp_var).pack(pady=4)

        tk.Label(win, text="Font size:").pack(pady=4)
        size_combo = ttk.Combobox(win, values=[str(s) for s in STANDARD_FONT_SIZES], width=5)
        size_combo.set(str(self.font_size))
        size_combo.pack(pady=4)

        def save():
            try:
                size = int(size_combo.get())
            except ValueError:
                return messagebox.showerror("Invalid", "Enter integer font size.")
            self.font_size = min(STANDARD_FONT_SIZES, key=lambda s: abs(s - size))
            self.base = base_var.get().strip() or self.base
            self.exponent = exp_var.get().strip() or self.exponent
            self.update_display()
            win.destroy()
            # Propagate new font size to the snapped group
            self.master.editor.propagate_font_size(self, self.font_size)

        tk.Button(win, text="Save", command=save).pack(pady=10)
        tk.Button(win, text="Delete", command=lambda: self.delete_and_close(win)).pack(pady=5)
        win.wait_window()
