import os
import subprocess
import json
import shutil
import tkinter as tk
from tkinter import Menu, filedialog, messagebox
from pdf2image import convert_from_path
from PIL import Image, ImageTk

def extract_math(expr):
    expr = expr.strip()
    first = expr.find("$")
    last = expr.rfind("$")
    if first != -1 and last != -1 and last > first:
        return expr[first+1:last]
    return expr

from blocks.exponent import ExponentBlock
from blocks.fraction import FractionBlock
from blocks.operation import OperationBlock
from blocks.nth_root import NthRootBlock

SNAP_DISTANCE = 5
VERTICAL_THRESHOLD = 10

class LaTeXEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("EzTeX")
        self.root.geometry("1400x900")
        self.blocks = []
        self.current_file = None
        self.preview_image = None
        self.code_text = None  # For "View Code" mode
        self.group_borders = []  # IDs of blue rectangles for snapped groups

        menubar = Menu(root)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_document)
        file_menu.add_command(label="Open", command=self.open_document)
        file_menu.add_command(label="Save", command=self.save_document)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        root.config(menu=menubar)

        self.setup_ui()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg="lightgray")
        self.main_frame.pack(fill="both", expand=True)

        self.editor_preview_frame = tk.Frame(self.main_frame, bg="lightgray")
        self.editor_preview_frame.pack(fill="both", expand=True)

        # Editor column:
        editor_column = tk.Frame(self.editor_preview_frame, bg="lightgray")
        editor_column.pack(side="left", expand=True, fill="both", padx=20, pady=20)

        editor_toolbar = tk.Frame(editor_column, bg="lightgray", height=40)
        editor_toolbar.pack(fill="x")
        tk.Button(editor_toolbar, text="Add Exponent", command=self.add_exponent, cursor="hand2").pack(side="left", padx=5)
        tk.Button(editor_toolbar, text="Add Fraction", command=self.add_fraction, cursor="hand2").pack(side="left", padx=5)
        tk.Button(editor_toolbar, text="Add Nth Root", command=self.add_nthroot, cursor="hand2").pack(side="left", padx=5)
        # Operation buttons (each creates an OperationBlock with fixed operator)
        tk.Button(editor_toolbar, text="+", command=lambda: self.add_operation("+"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="-", command=lambda: self.add_operation("-"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="·", command=lambda: self.add_operation("x"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="/", command=lambda: self.add_operation("/"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="=", command=lambda: self.add_operation("="), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="∑", command=lambda: self.add_operation("∑"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="∏", command=lambda: self.add_operation("∏"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="∫", command=lambda: self.add_operation("∫"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="(", command=lambda: self.add_operation("("), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text=")", command=lambda: self.add_operation(")"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="log", command=lambda: self.add_operation("log"), cursor="hand2").pack(side="left", padx=2)
        tk.Button(editor_toolbar, text="ln", command=lambda: self.add_operation("ln"), cursor="hand2").pack(side="left", padx=2)



        self.editor_page_frame = tk.Frame(editor_column, bg="white", bd=2, relief="ridge")
        self.editor_page_frame.pack(expand=True, fill="both", pady=(5,0))

        # Changed from width=800, height=1100 to bigger size (e.g. 800×1000)
        self.editor_canvas = tk.Canvas(self.editor_page_frame, width=800, height=1000, bg="white")
        self.editor_canvas.pack()
        self.editor_canvas.editor = self

        # Preview column:
        preview_column = tk.Frame(self.editor_preview_frame, bg="lightgray")
        preview_column.pack(side="left", expand=True, fill="both", padx=20, pady=20)

        preview_toolbar = tk.Frame(preview_column, bg="lightgray", height=40)
        preview_toolbar.pack(fill="x")
        tk.Button(preview_toolbar, text="Preview LaTeX", command=self.preview_latex).pack(side="left", padx=5)
        tk.Button(preview_toolbar, text="View Code", command=self.view_code).pack(side="left", padx=5)
        tk.Button(preview_toolbar, text="Export PDF", command=self.export_pdf).pack(side="left", padx=5)

        self.preview_page_frame = tk.Frame(preview_column, bg="white", bd=2, relief="ridge")
        self.preview_page_frame.pack(expand=True, fill="both", pady=(5,0))

        # Make the preview canvas match the editor canvas size
        self.preview_canvas = tk.Canvas(self.preview_page_frame, width=800, height=1000, bg="white")
        self.preview_canvas.pack()
        self.preview_canvas.editor = self


    def update_group_borders(self):
        # Clear existing borders.
        for rect in self.group_borders:
            self.editor_canvas.delete(rect)
        self.group_borders = []
        groups = self.get_groups()
        for group in groups:
            if len(group) > 1:
                xs = [b.widget.winfo_x() for b in group]
                ys = [b.widget.winfo_y() for b in group]
                widths = [b.widget.winfo_width() for b in group]
                heights = [b.widget.winfo_height() for b in group]
                min_x = min(xs)
                min_y = min(ys)
                max_x = max(x+w for x,w in zip(xs,widths))
                max_y = max(y+h for y,h in zip(ys,heights))
                pad = 2
                rect = self.editor_canvas.create_rectangle(min_x-pad, min_y-pad, max_x+pad, max_y+pad,
                                                             outline="blue", width=2)
                self.editor_canvas.tag_lower(rect)
                self.group_borders.append(rect)

    def find_free_position(self, default_x, default_y, block_width, block_height):
        x, y = default_x, default_y
        overlap = True
        while overlap:
            overlap = False
            for b in self.blocks:
                bx = b.widget.winfo_x()
                by = b.widget.winfo_y()
                bw = b.widget.winfo_width()
                bh = b.widget.winfo_height()
                if (x < bx + bw and x + block_width > bx and
                    y < by + bh and y + block_height > by):
                    overlap = True
                    x += 10
                    y += 10
                    break
        return x, y

    def get_groups(self):
        visited = set()
        groups = []
        for b in self.blocks:
            if b in visited:
                continue
            stack = [b]
            group = [b]
            visited.add(b)
            while stack:
                cur = stack.pop()
                cx, cy = cur.widget.winfo_x(), cur.widget.winfo_y()
                cw = cur.widget.winfo_width()
                for other in self.blocks:
                    if other in visited:
                        continue
                    ox, oy = other.widget.winfo_x(), other.widget.winfo_y()
                    ow = other.widget.winfo_width()
                    if abs(cx+cw-ox) < SNAP_DISTANCE and abs(cy-oy) < VERTICAL_THRESHOLD:
                        visited.add(other)
                        stack.append(other)
                        group.append(other)
                    elif abs(cx - (ox+ow)) < SNAP_DISTANCE and abs(cy-oy) < VERTICAL_THRESHOLD:
                        visited.add(other)
                        stack.append(other)
                        group.append(other)
            groups.append(sorted(group, key=lambda blk: blk.widget.winfo_x()))
        return groups

    def gather_latex(self):
        groups = self.get_groups()
        if not groups:
            return r"\mbox{}"
        lines = [r"\setlength{\unitlength}{1pt}", r"\begin{picture}(800,1100)"]
        for group in groups:
            sorted_group = sorted(group, key=lambda blk: blk.widget.winfo_x())
            first_block = sorted_group[0]
            x = first_block.widget.winfo_x()
            y_inv = 1100 - first_block.widget.winfo_y()
            wrap_in_parens = (isinstance(sorted_group[0], OperationBlock) and sorted_group[0].operation=="(" and
                              isinstance(sorted_group[-1], OperationBlock) and sorted_group[-1].operation==")")
            if wrap_in_parens:
                sorted_group = sorted_group[1:-1]
            if any(isinstance(b, OperationBlock) and b.operation == "/" for b in sorted_group):
                left, right = [], []
                found_slash = False
                for b in sorted_group:
                    if isinstance(b, OperationBlock) and b.operation == "/":
                        found_slash = True
                        continue
                    if not found_slash:
                        left.append(b)
                    else:
                        right.append(b)
                left_content = "".join(b.get_latex().strip() for b in left)
                right_content = "".join(b.get_latex().strip() for b in right)
                combined_expr = rf"\frac{{{left_content}}}{{{right_content}}}"
            else:
                combined_expr = "".join(b.get_latex().strip() for b in sorted_group)
            if wrap_in_parens:
                combined_expr = rf"\left({combined_expr}\right)"
            combined_wrapped = rf"\fontsize{{{first_block.font_size}pt}}{{{first_block.font_size+2}pt}}\selectfont ${combined_expr}$"
            lines.append(fr"\put({x},{y_inv}){{\makebox(0,0)[lt]{{{combined_wrapped}}}}}")
        lines.append(r"\end{picture}")
        return "\n".join(lines)

    def new_document(self):
        for b in self.blocks:
            b.widget.destroy()
        self.blocks.clear()
        self.editor_canvas.delete("all")
        self.current_file = None

    def delete_block(self, block):
        if block in self.blocks:
            self.blocks.remove(block)
            block.widget.destroy()

    def save_document(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("EZLaTeX Files", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        try:
            blocks_data = []
            for b in self.blocks:
                block_dict = {"x": b.widget.winfo_x(),
                              "y": b.widget.winfo_y(),
                              "font_size": b.font_size}
                if hasattr(b, "base") and hasattr(b, "exponent"):
                    block_dict["type"] = "exponent"
                    block_dict["base"] = b.base
                    block_dict["exponent"] = b.exponent
                elif hasattr(b, "numerator") and hasattr(b, "denominator"):
                    block_dict["type"] = "fraction"
                    block_dict["numerator"] = b.numerator
                    block_dict["denominator"] = b.denominator
                elif hasattr(b, "operation"):
                    block_dict["type"] = "operation"
                    block_dict["operation"] = b.operation
                elif hasattr(b, "radicand") and hasattr(b, "degree"):
                    block_dict["type"] = "nthroot"
                    block_dict["radicand"] = b.radicand
                    block_dict["degree"] = b.degree
                else:
                    continue
                blocks_data.append(block_dict)
            data = {"blocks": blocks_data}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.current_file = path
            messagebox.showinfo("Save", "File saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def open_document(self):
        path = filedialog.askopenfilename(filetypes=[("EZLaTeX Files", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.new_document()
            for entry in data["blocks"]:
                typ = entry.get("type")
                if typ == "exponent":
                    b = ExponentBlock(self.editor_canvas, entry.get("base", "x"),
                                      entry.get("exponent", "2"), entry.get("font_size", 10))
                elif typ == "fraction":
                    b = FractionBlock(self.editor_canvas, entry.get("numerator", "1"),
                                      entry.get("denominator", "2"), entry.get("font_size", 10))
                elif typ == "operation":
                    b = OperationBlock(self.editor_canvas, entry.get("operation", "+"), entry.get("font_size", 10))
                elif typ == "nthroot":
                    b = NthRootBlock(self.editor_canvas, entry.get("radicand", "x"),
                                     entry.get("degree", "2"), entry.get("font_size", 10))
                else:
                    continue
                b.widget.place(x=entry.get("x", 0), y=entry.get("y", 0))
                self.blocks.append(b)
            self.current_file = path
            messagebox.showinfo("Open", "File loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")

    def add_exponent(self):
        b = ExponentBlock(self.editor_canvas)
        self.editor_canvas.update_idletasks()
        bw = b.widget.winfo_width()
        bh = b.widget.winfo_height()
        x, y = self.find_free_position(50, 50, bw, bh)
        b.widget.place(x=x, y=y)
        self.blocks.append(b)
        self.update_group_borders()

    def add_fraction(self):
        b = FractionBlock(self.editor_canvas)
        self.editor_canvas.update_idletasks()
        bw = b.widget.winfo_width()
        bh = b.widget.winfo_height()
        x, y = self.find_free_position(50, 150, bw, bh)
        b.widget.place(x=x, y=y)
        self.blocks.append(b)
        self.update_group_borders()

    def add_operation(self, op="+"):
        b = OperationBlock(self.editor_canvas, operation=op)
        self.editor_canvas.update_idletasks()
        bw = b.widget.winfo_width()
        bh = b.widget.winfo_height()
        x, y = self.find_free_position(50, 250, bw, bh)
        b.widget.place(x=x, y=y)
        self.blocks.append(b)
        self.update_group_borders()

    def add_nthroot(self):
        b = NthRootBlock(self.editor_canvas)
        self.editor_canvas.update_idletasks()
        bw = b.widget.winfo_width()
        bh = b.widget.winfo_height()
        x, y = self.find_free_position(50, 350, bw, bh)
        b.widget.place(x=x, y=y)
        self.blocks.append(b)
        self.update_group_borders()

    def compile_latex_to_pdf(self, latex):
        tex = rf"""\documentclass[letterpaper]{{article}}
\usepackage[paperwidth=800pt,paperheight=1100pt,margin=0pt]{{geometry}}
\usepackage{{amsmath,anyfontsize}}
\pagestyle{{empty}}
\begin{{document}}
{latex}
\end{{document}}"""
        with open("preview.tex", "w", encoding="utf-8") as f:
            f.write(tex)
        try:
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "preview.tex"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            messagebox.showerror("Error", "LaTeX compilation failed.")
            return None
        return "preview.pdf" if os.path.exists("preview.pdf") else None

    def preview_latex(self):
        if self.code_text is not None:
            self.code_text.destroy()
            self.code_text = None
        pdf = self.compile_latex_to_pdf(self.gather_latex())
        if not pdf:
            return
        img = convert_from_path(pdf, first_page=1, last_page=1)[0]
        img.thumbnail((800,1100))
        self.preview_image = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image((800-img.width)//2, (1100-img.height)//2,
                                         anchor="nw", image=self.preview_image)

    def view_code(self):
        body = self.gather_latex()
        tex = rf"""\documentclass[letterpaper]{{article}}
\usepackage[paperwidth=800pt,paperheight=1100pt,margin=0pt]{{geometry}}
\usepackage{{amsmath,anyfontsize}}
\pagestyle{{empty}}
\begin{{document}}
{body}
\end{{document}}"""
        self.preview_canvas.delete("all")
        self.preview_image = None
        if self.code_text is not None:
            self.code_text.destroy()
        self.code_text = tk.Text(self.preview_canvas, wrap="none", font=("Courier", 10))
        self.code_text.insert("1.0", tex)
        self.code_text.config(state="disabled")
        self.preview_canvas.create_window(0, 0, anchor="nw", window=self.code_text, width=800, height=1100)

    def export_pdf(self):
        pdf = self.compile_latex_to_pdf(self.gather_latex())
        if not pdf:
            return
        export_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                   filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
        if not export_path:
            return
        try:
            shutil.copyfile(pdf, export_path)
            messagebox.showinfo("Export", "PDF exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF:\n{str(e)}")

    def propagate_font_size(self, edited_block, new_font_size):
        groups = self.get_groups()
        target_group = None
        for group in groups:
            if edited_block in group:
                target_group = group
                break
        if not target_group:
            return
        for block in target_group:
            block.font_size = new_font_size
            block.update_display()
        self.reposition_group(target_group)
        self.update_group_borders()  # Update blue border after font change.


    def reposition_group(self, group):
        sorted_group = sorted(group, key=lambda b: b.widget.winfo_x())
        common_y = min(b.widget.winfo_y() for b in sorted_group)
        x = sorted_group[0].widget.winfo_x()
        for block in sorted_group:
            block.widget.place(x=x, y=common_y)
            block.widget.update_idletasks()
            x += block.widget.winfo_width()  # no gap between blocks


if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')
    LaTeXEditor(root)
    root.mainloop()