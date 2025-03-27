import tkinter as tk
from tkinter import ttk, messagebox
from .base import Block, DISPLAY_FONT_SCALE, STANDARD_FONT_SIZES, MODAL_OFFSET

class OperationBlock(Block):
    def __init__(self, master, operation="+", font_size=10):
        self.operation = operation  # fixed at creation time
        # For summation, initialize lower and upper limits with defaults.
        if self.operation == "∑":
            self.lower_limit = "i=1"
            self.upper_limit = "n"
        # For log, set default base and argument.
        if self.operation.lower() == "log":
            self.log_base = "10"
            self.log_argument = ""
        # For ln, just set an empty argument.
        if self.operation.lower() == "ln":
            self.log_argument = ""
        super().__init__(master, text=operation, font_size=font_size)

    def get_latex(self):
        op_lower = self.operation.lower()
        if op_lower == "x":
            return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \cdot}}"
        elif self.operation == "/":
            return ""
        elif self.operation == "(":
            # Return raw commands without font size or math mode delimiters.
            return r"\left("
        elif self.operation == ")":
            return r"\right)"
        elif op_lower == "log":
            # If no argument, output just the function name (with optional subscript if base != "10")
            if self.log_argument:
                if self.log_base == "10":
                    return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \log\left({self.log_argument}\right)}}"
                else:
                    return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \log_{{{self.log_base}}}\left({self.log_argument}\right)}}"
            else:
                if self.log_base == "10":
                    return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \log}}"
                else:
                    return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \log_{{{self.log_base}}}}}"
        elif op_lower == "ln":
            if self.log_argument:
                return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \ln\left({self.log_argument}\right)}}"
            else:
                return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \ln}}"
        elif self.operation == "∑":
            return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \sum_{{{self.lower_limit}}}^{{{self.upper_limit}}}}}"
        elif self.operation == "∏":
            return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \prod}}"
        elif self.operation == "∫":
            return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ \int}}"
        else:
            return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont \!\ {self.operation}}}"

    def update_display(self):
        display = self.font_size if self.font_size <= 16 else int(self.font_size * DISPLAY_FONT_SCALE)
        op_lower = self.operation.lower()
        if op_lower == "x":
            text = "·"
        elif op_lower in ["log", "ln"]:
            # For display purposes, show "log" or "ln" with the argument if provided.
            if self.log_argument:
                if op_lower == "log" and self.log_base != "10":
                    text = f"log₍{self.log_base}₎({self.log_argument})"
                else:
                    text = f"{self.operation}({self.log_argument})"
            else:
                text = self.operation
        elif self.operation == "∑":
            text = "∑"
        else:
            text = self.operation
        self.widget.config(text=text, font=("Helvetica", display))

    def delete_and_close(self, win):
        self.master.editor.delete_block(self)
        win.destroy()

    def edit(self, event):
        win = tk.Toplevel(self.master.winfo_toplevel())
        # Title based on the operator.
        win.title("Edit Operation")
        win.geometry(f"+{self.widget.winfo_rootx()+MODAL_OFFSET}+{self.widget.winfo_rooty()+MODAL_OFFSET}")
        win.transient(self.master.winfo_toplevel())
        win.grab_set()

        op_lower = self.operation.lower()
        if op_lower == "∑":
            tk.Label(win, text="Operator: ∑").pack(pady=4)
            tk.Label(win, text="Lower Limit:").pack(pady=4)
            lower_var = tk.StringVar(value=self.lower_limit)
            tk.Entry(win, textvariable=lower_var, width=10).pack(pady=4)
            tk.Label(win, text="Upper Limit:").pack(pady=4)
            upper_var = tk.StringVar(value=self.upper_limit)
            tk.Entry(win, textvariable=upper_var, width=10).pack(pady=4)
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
                self.lower_limit = lower_var.get().strip() or self.lower_limit
                self.upper_limit = upper_var.get().strip() or self.upper_limit
                self.update_display()
                win.destroy()
                self.master.editor.propagate_font_size(self, self.font_size)
            tk.Button(win, text="Save", command=save).pack(pady=10)
            tk.Button(win, text="Delete", command=lambda: self.delete_and_close(win)).pack(pady=5)
        elif op_lower in ["log", "ln"]:
            tk.Label(win, text=f"Operator: {self.operation}").pack(pady=4)
            if op_lower == "log":
                tk.Label(win, text="Base (default 10):").pack(pady=4)
                base_var = tk.StringVar(value=self.log_base)
                tk.Entry(win, textvariable=base_var, width=10).pack(pady=4)
            tk.Label(win, text="Argument:").pack(pady=4)
            arg_var = tk.StringVar(value=self.log_argument)
            tk.Entry(win, textvariable=arg_var, width=10).pack(pady=4)
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
                if op_lower == "log":
                    new_base = base_var.get().strip()
                    self.log_base = new_base if new_base and new_base != "10" else "10"
                self.log_argument = arg_var.get().strip()
                self.update_display()
                win.destroy()
                self.master.editor.propagate_font_size(self, self.font_size)
            tk.Button(win, text="Save", command=save).pack(pady=10)
            tk.Button(win, text="Delete", command=lambda: self.delete_and_close(win)).pack(pady=5)
        else:
            tk.Label(win, text=f"Operator: {self.operation}").pack(pady=4)
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
                self.update_display()
                win.destroy()
                self.master.editor.propagate_font_size(self, self.font_size)
            tk.Button(win, text="Save", command=save).pack(pady=10)
            tk.Button(win, text="Delete", command=lambda: self.delete_and_close(win)).pack(pady=5)
        win.wait_window()
