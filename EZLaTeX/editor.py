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
        self.code_text = None  # For the "View Code" mode

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

        # Editor column
        editor_column = tk.Frame(self.editor_preview_frame, bg="lightgray")
        editor_column.pack(side="left", expand=True, fill="both", padx=20, pady=20)

        editor_toolbar = tk.Frame(editor_column, bg="lightgray", height=40)
        editor_toolbar.pack(fill="x")
        tk.Button(editor_toolbar, text="Add Exponent", command=self.add_exponent).pack(side="left", padx=5)
        tk.Button(editor_toolbar, text="Add Fraction", command=self.add_fraction).pack(side="left", padx=5)
        tk.Button(editor_toolbar, text="Add Operation", command=self.add_operation).pack(side="left", padx=5)

        self.editor_page_frame = tk.Frame(editor_column, bg="white", bd=2, relief="ridge")
        self.editor_page_frame.pack(expand=True, fill="both", pady=(5,0))
        self.editor_canvas = tk.Canvas(self.editor_page_frame, width=612, height=792, bg="white")
        self.editor_canvas.pack()
        self.editor_canvas.editor = self

        # Preview column
        preview_column = tk.Frame(self.editor_preview_frame, bg="lightgray")
        preview_column.pack(side="left", expand=True, fill="both", padx=20, pady=20)

        preview_toolbar = tk.Frame(preview_column, bg="lightgray", height=40)
        preview_toolbar.pack(fill="x")
        tk.Button(preview_toolbar, text="Preview LaTeX", command=self.preview_latex).pack(side="left", padx=5)
        tk.Button(preview_toolbar, text="View Code", command=self.view_code).pack(side="left", padx=5)
        tk.Button(preview_toolbar, text="Export PDF", command=self.export_pdf).pack(side="left", padx=5)

        self.preview_page_frame = tk.Frame(preview_column, bg="white", bd=2, relief="ridge")
        self.preview_page_frame.pack(expand=True, fill="both", pady=(5,0))
        self.preview_canvas = tk.Canvas(self.preview_page_frame, width=612, height=792, bg="white")
        self.preview_canvas.pack()
        self.preview_canvas.editor = self

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
                    if abs(cx + cw - ox) < SNAP_DISTANCE and abs(cy - oy) < VERTICAL_THRESHOLD:
                        visited.add(other)
                        stack.append(other)
                        group.append(other)
                    elif abs(cx - (ox + ow)) < SNAP_DISTANCE and abs(cy - oy) < VERTICAL_THRESHOLD:
                        visited.add(other)
                        stack.append(other)
                        group.append(other)
            groups.append(sorted(group, key=lambda blk: blk.widget.winfo_x()))
        return groups

    def gather_latex(self):
        groups = self.get_groups()
        if not groups:
            return r"\mbox{}"
        lines = [r"\setlength{\unitlength}{1pt}", r"\begin{picture}(612,792)"]
        for group in groups:
            # Check if the group contains an OperationBlock with "/" as the operation.
            if any(isinstance(b, OperationBlock) and b.operation == "/" for b in group):
                # Partition group into left and right parts around the first "/" operator.
                left, right = [], []
                found_slash = False
                for b in group:
                    if isinstance(b, OperationBlock) and b.operation == "/":
                        found_slash = True
                        continue
                    if not found_slash:
                        left.append(b)
                    else:
                        right.append(b)
                # Extract plain math content from left and right parts.
                left_content = "".join(extract_math(b.get_latex().strip()) for b in left)
                right_content = "".join(extract_math(b.get_latex().strip()) for b in right)
                first = left[0] if left else group[0]
                x = first.widget.winfo_x()
                y_inv = 792 - first.widget.winfo_y()
                # Form a single fraction without nested $ signs.
                combined = rf"\frac{{{left_content}}}{{{right_content}}}"
                # Wrap the combined fraction in math mode once.
                lines.append(fr"\put({x},{y_inv}){{\makebox(0,0)[lt]{{\fontsize{{{first.font_size}pt}}{{{first.font_size+2}pt}}\selectfont ${combined}$}}}}")
            else:
                sorted_group = sorted(group, key=lambda blk: blk.widget.winfo_x())
                first = sorted_group[0]
                x = first.widget.winfo_x()
                y_inv = 792 - first.widget.winfo_y()
                combined = "".join(b.get_latex().strip() for b in sorted_group)
                lines.append(fr"\put({x},{y_inv}){{\makebox(0,0)[lt]{{{combined}}}}}")
        lines.append(r"\end{picture}")
        return "\n".join(lines)



    def new_document(self):
        # Destroy all block widgets from the canvas
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
                block_dict = {
                    "x": b.widget.winfo_x(),
                    "y": b.widget.winfo_y(),
                    "font_size": b.font_size
                }
                if isinstance(b, ExponentBlock):
                    block_dict["type"] = "exponent"
                    block_dict["base"] = b.base
                    block_dict["exponent"] = b.exponent
                elif isinstance(b, FractionBlock):
                    block_dict["type"] = "fraction"
                    block_dict["numerator"] = b.numerator
                    block_dict["denominator"] = b.denominator
                elif isinstance(b, OperationBlock):
                    block_dict["type"] = "operation"
                    block_dict["operation"] = b.operation
                else:
                    continue  # unknown block type
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
                else:
                    continue  # unknown block type; skip
                b.widget.place(x=entry.get("x", 0), y=entry.get("y", 0))
                self.blocks.append(b)
            self.current_file = path
            messagebox.showinfo("Open", "File loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")

    def add_exponent(self):
        b = ExponentBlock(self.editor_canvas)
        b.widget.place(x=50, y=50)
        self.blocks.append(b)

    def add_fraction(self):
        b = FractionBlock(self.editor_canvas)
        b.widget.place(x=50, y=150)
        self.blocks.append(b)

    def add_operation(self):
        b = OperationBlock(self.editor_canvas)
        b.widget.place(x=50, y=250)
        self.blocks.append(b)

    def compile_latex_to_pdf(self, latex):
        tex = rf"""\documentclass[letterpaper]{{article}}
\usepackage[paperwidth=612pt,paperheight=792pt,margin=0pt]{{geometry}}
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
        # Remove any code view widget if it exists
        if self.code_text is not None:
            self.code_text.destroy()
            self.code_text = None
        pdf = self.compile_latex_to_pdf(self.gather_latex())
        if not pdf:
            return
        img = convert_from_path(pdf, first_page=1, last_page=1)[0]
        img.thumbnail((612,792))
        self.preview_image = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image((612-img.width)//2, (792-img.height)//2,
                                         anchor="nw", image=self.preview_image)

    def view_code(self):
        # Generate the LaTeX source code (same as what gets written to preview.tex)
        body = self.gather_latex()
        tex = rf"""\documentclass[letterpaper]{{article}}
\usepackage[paperwidth=612pt,paperheight=792pt,margin=0pt]{{geometry}}
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
        self.preview_canvas.create_window(0, 0, anchor="nw", window=self.code_text, width=612, height=792)

    def export_pdf(self):
        # Generate the LaTeX source and compile into a PDF
        pdf = self.compile_latex_to_pdf(self.gather_latex())
        if not pdf:
            return
        # Prompt the user for a destination filename for the PDF
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

    def reposition_group(self, group):
        sorted_group = sorted(group, key=lambda b: b.widget.winfo_x())
        common_y = min(b.widget.winfo_y() for b in sorted_group)
        margin = 5
        x = sorted_group[0].widget.winfo_x()
        for block in sorted_group:
            block.widget.place(x=x, y=common_y)
            block.widget.update_idletasks()
            block_width = block.widget.winfo_width()
            x += block_width + margin

        canvas_width = self.editor_canvas.winfo_width()
        last_block = sorted_group[-1]
        right_edge = last_block.widget.winfo_x() + last_block.widget.winfo_width()
        if right_edge > canvas_width:
            shift = right_edge - canvas_width
            for block in sorted_group:
                current_x = block.widget.winfo_x()
                new_x = max(0, current_x - shift)
                block.widget.place(x=new_x, y=common_y)

if __name__ == "__main__":
    root = tk.Tk()
    LaTeXEditor(root)
    root.mainloop()
