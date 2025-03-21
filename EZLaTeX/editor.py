import os
import subprocess
import json
import tkinter as tk
from tkinter import Menu, filedialog, messagebox
from pdf2image import convert_from_path
from PIL import Image, ImageTk

from blocks.exponent import ExponentBlock
from blocks.fraction import FractionBlock
from blocks.operation import OperationBlock

class LaTeXEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("LaTeX Editor for Ontario Math")
        self.root.geometry("1400x900")
        self.blocks = []
        self.current_file = None
        self.preview_image = None

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

        self.preview_page_frame = tk.Frame(preview_column, bg="white", bd=2, relief="ridge")
        self.preview_page_frame.pack(expand=True, fill="both", pady=(5,0))
        self.preview_canvas = tk.Canvas(self.preview_page_frame, width=612, height=792, bg="white")
        self.preview_canvas.pack()
        self.preview_canvas.editor = self

    def new_document(self):
        self.blocks.clear()
        self.editor_canvas.delete("all")
        self.current_file = None

    def save_document(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("EZLaTeX Files","*.json"), ("All Files","*.*")])
        if not path:
            return

        data = []
        for b in self.blocks:
            entry = {"type": b.__class__.__name__.replace("Block","").lower(),
                     "x": b.widget.winfo_x(), "y": b.widget.winfo_y(), "font_size": b.font_size}
            if isinstance(b, ExponentBlock):
                entry["base"], entry["exponent"] = b.base, b.exponent
            elif isinstance(b, FractionBlock):
                entry.update(numerator=b.numerator, denominator=b.denominator)
            else:
                entry["operation"] = b.operation
            data.append(entry)

        with open(path, "w") as f:
            json.dump({"blocks": data}, f)
        self.current_file = path

    def open_document(self):
        path = filedialog.askopenfilename(filetypes=[("EZLaTeX Files","*.json"), ("All Files","*.*")])
        if not path:
            return

        with open(path) as f:
            obj = json.load(f)

        self.new_document()
        for entry in obj["blocks"]:
            typ = entry["type"]
            if typ == "exponent":
                b = ExponentBlock(self.editor_canvas, entry["base"], entry["exponent"], entry["font_size"])
            elif typ == "fraction":
                b = FractionBlock(self.editor_canvas, entry["numerator"], entry["denominator"], entry["font_size"])
            else:
                b = OperationBlock(self.editor_canvas, entry["operation"], entry["font_size"])
            b.widget.place(x=entry["x"], y=entry["y"])
            self.blocks.append(b)

        self.current_file = path

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

    def gather_latex(self):
        if not self.blocks:
            return r"\mbox{}"
        lines = [r"\setlength{\unitlength}{1pt}", r"\begin{picture}(612,792)"]
        for b in self.blocks:
            x, y = b.widget.winfo_x(), 792 - b.widget.winfo_y()
            blk = b.get_latex().strip()
            if blk:
                lines.append(fr"\put({x},{y}){{\makebox(0,0)[lt]{{{blk}}}}}")
        lines.append(r"\end{picture}")
        return "\n".join(lines)

    def compile_latex_to_pdf(self, latex):
        tex = rf"""\documentclass[letterpaper]{{article}}
\usepackage[paperwidth=612pt,paperheight=792pt,margin=0pt]{{geometry}}
\usepackage{{amsmath,anyfontsize}}
\pagestyle{{empty}}
\begin{{document}}
{latex}
\end{{document}}"""
        with open("preview.tex","w", encoding="utf-8") as f:
            f.write(tex)
        try:
            subprocess.run(["pdflatex","-interaction=nonstopmode","preview.tex"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            messagebox.showerror("Error","LaTeX compilation failed.")
            return None
        return "preview.pdf" if os.path.exists("preview.pdf") else None

    def preview_latex(self):
        pdf = self.compile_latex_to_pdf(self.gather_latex())
        if not pdf:
            return
        img = convert_from_path(pdf, first_page=1, last_page=1)[0]
        img.thumbnail((612,792))
        self.preview_image = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image((612-img.width)//2, (792-img.height)//2,
                                         anchor="nw", image=self.preview_image)

if __name__ == "__main__":
    root = tk.Tk()
    LaTeXEditor(root)
    root.mainloop()
