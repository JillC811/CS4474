import tkinter as tk
from tkinter import ttk, messagebox
from .base import Block, DISPLAY_FONT_SCALE, STANDARD_FONT_SIZES, MODAL_OFFSET

class NthRootBlock(Block):
    def __init__(self, master, radicand="x", degree="2", font_size=10):
        self.radicand = radicand
        self.degree = degree
        # Set the initial text representation (for dragging) based on radicand and degree.
        super().__init__(master, text=f"√[{degree}]{{{radicand}}}", font_size=font_size)

    def get_latex(self):
        # Return raw LaTeX (without surrounding $ ... $) for an nth root.
        # Format: \sqrt[degree]{radicand}
        return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \sqrt[{self.degree}]{{{self.radicand}}}}}"

    def update_display(self):
        display = self.font_size if self.font_size <= 16 else int(self.font_size * DISPLAY_FONT_SCALE)
        # Update the widget text to show the current radicand and degree.
        self.widget.config(text=f"√[{self.degree}]{{{self.radicand}}}", font=("Helvetica", display))

    def delete_and_close(self, win):
        self.master.editor.delete_block(self)
        win.destroy()

    def edit(self, event):
        # Open a dialog to let the user edit both the radicand and the degree.
        win = tk.Toplevel(self.master.winfo_toplevel())
        win.title("Edit Nth Root")
        win.geometry(f"+{self.widget.winfo_rootx()+MODAL_OFFSET}+{self.widget.winfo_rooty()+MODAL_OFFSET}")
        win.transient(self.master.winfo_toplevel())
        win.grab_set()

        tk.Label(win, text="Radicand:").pack(pady=4)
        radicand_var = tk.StringVar(value=self.radicand)
        tk.Entry(win, textvariable=radicand_var, width=10).pack(pady=4)

        tk.Label(win, text="Degree:").pack(pady=4)
        degree_var = tk.StringVar(value=self.degree)
        tk.Entry(win, textvariable=degree_var, width=10).pack(pady=4)

        tk.Label(win, text="Font size:").pack(pady=4)
        size_combo = ttk.Combobox(win, values=[str(s) for s in STANDARD_FONT_SIZES], width=5)
        size_combo.set(str(self.font_size))
        size_combo.pack(pady=4)

        def save():
            try:
                size = int(size_combo.get())
            except ValueError:
                return messagebox.showerror("Invalid", "Enter an integer font size.")
            self.font_size = min(STANDARD_FONT_SIZES, key=lambda s: abs(s - size))
            self.radicand = radicand_var.get().strip() or self.radicand
            self.degree = degree_var.get().strip() or self.degree
            self.update_display()
            win.destroy()
            self.master.editor.propagate_font_size(self, self.font_size)

        tk.Button(win, text="Save", command=save).pack(pady=10)
        tk.Button(win, text="Delete", command=lambda: self.delete_and_close(win)).pack(pady=5)
        win.wait_window()
