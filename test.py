import tkinter as tk
from tkinter import simpledialog, messagebox, Menu, ttk, filedialog
import subprocess, os, json
from pdf2image import convert_from_path
from PIL import Image, ImageTk

DISPLAY_FONT_SCALE = 0.85
STANDARD_FONT_SIZES = [8,9,10,11,12,14,16,18,20,22,24,26,28,36]
MODAL_OFFSET = 10

class Block:
    def __init__(self, master, text="Block", font_size=10):
        self.master = master
        self.text = text
        self.font_size = font_size
        display_size = self.font_size if self.font_size <= 16 else int(self.font_size * DISPLAY_FONT_SCALE)
        self.widget = tk.Label(master, text=text, bg="lightgray", relief="raised",
                               padx=5, pady=5, font=("Helvetica", display_size), anchor="nw")
        self.widget.bind("<Button-1>", self.on_click)
        self.widget.bind("<B1-Motion>", self.on_drag)
        self.widget.bind("<Double-Button-1>", self.edit)
        self.offset_x = self.offset_y = 0

    def on_click(self, e):
        self.offset_x, self.offset_y = e.x, e.y

    def on_drag(self, e):
        new_x = self.widget.winfo_x() + e.x - self.offset_x
        new_y = self.widget.winfo_y() + e.y - self.offset_y
        pw, ph = self.master.winfo_width(), self.master.winfo_height()
        ww, wh = self.widget.winfo_width(), self.widget.winfo_height()
        self.master.update_idletasks()
        self.widget.place(x=max(0, min(new_x, pw-ww)), y=max(0, min(new_y, ph-wh)))

    def get_latex(self): return ""

class EquationBlock(Block):
    def __init__(self, master, equation="x^2 + y^2 = z^2", font_size=10):
        self.equation = equation
        super().__init__(master, text=equation, font_size=font_size)

    def get_latex(self):
        return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont $\!\ {self.equation}$}}"

    def edit(self, event):
        win = tk.Toplevel(self.master.winfo_toplevel()); win.title("Edit Equation")
        x = self.widget.winfo_rootx() + MODAL_OFFSET; y = self.widget.winfo_rooty() + MODAL_OFFSET
        win.geometry(f"+{x}+{y}"); win.transient(self.master.winfo_toplevel()); win.grab_set()

        tk.Label(win, text="Equation:").pack(pady=4)
        eq_var = tk.StringVar(value=self.equation)
        tk.Entry(win, textvariable=eq_var, width=30).pack(pady=4)

        tk.Label(win, text="Font size:").pack(pady=4)
        combo = ttk.Combobox(win, values=[str(s) for s in STANDARD_FONT_SIZES], width=5)
        combo.set(str(self.font_size)); combo.pack(pady=4)

        def save():
            try: entered = int(combo.get())
            except: 
                messagebox.showerror("Invalid","Enter integer font size."); return
            self.font_size = min(STANDARD_FONT_SIZES, key=lambda s: abs(s-entered))
            self.equation = eq_var.get().strip() or self.equation
            display = self.font_size if self.font_size<=16 else int(self.font_size*DISPLAY_FONT_SCALE)
            self.widget.config(text=self.equation, font=("Helvetica", display))
            win.destroy()

        tk.Button(win, text="Save", command=save).pack(pady=10)
        win.wait_window()

class FractionBlock(Block):
    def __init__(self, master, numerator="1", denominator="2", font_size=10):
        self.numerator, self.denominator = numerator, denominator
        super().__init__(master, text=f"{numerator}/{denominator}", font_size=font_size)

    def get_latex(self):
        return rf"{{\fontsize{{{self.font_size}pt}}{{{self.font_size+2}pt}}\selectfont $\!\ \frac{{{self.numerator}}}{{{self.denominator}}}$}}"

    def edit(self, event):
        win = tk.Toplevel(self.master.winfo_toplevel()); win.title("Edit Fraction")
        x = self.widget.winfo_rootx() + MODAL_OFFSET; y = self.widget.winfo_rooty() + MODAL_OFFSET
        win.geometry(f"+{x}+{y}"); win.transient(self.master.winfo_toplevel()); win.grab_set()

        tk.Label(win, text="Numerator:").pack(pady=4)
        num_var = tk.StringVar(value=self.numerator)
        tk.Entry(win, textvariable=num_var, width=10).pack(pady=4)

        tk.Label(win, text="Denominator:").pack(pady=4)
        den_var = tk.StringVar(value=self.denominator)
        tk.Entry(win, textvariable=den_var, width=10).pack(pady=4)

        tk.Label(win, text="Font size:").pack(pady=4)
        combo = ttk.Combobox(win, values=[str(s) for s in STANDARD_FONT_SIZES], width=5)
        combo.set(str(self.font_size)); combo.pack(pady=4)

        def save():
            try: entered = int(combo.get())
            except:
                messagebox.showerror("Invalid","Enter integer font size."); return
            self.font_size = min(STANDARD_FONT_SIZES, key=lambda s: abs(s-entered))
            self.numerator = num_var.get().strip() or self.numerator
            self.denominator = den_var.get().strip() or self.denominator
            display = self.font_size if self.font_size<=16 else int(self.font_size*DISPLAY_FONT_SCALE)
            self.widget.config(text=f"{self.numerator}/{self.denominator}", font=("Helvetica", display))
            win.destroy()

        tk.Button(win, text="Save", command=save).pack(pady=10)
        win.wait_window()

class LaTeXEditor:
    """
    The main LaTeX editor class.
    Manages the user interface, block placement, and LaTeX preview.
    Uses a picture environment for absolute positioning.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("LaTeX Editor for Ontario Math")
        self.root.geometry("1400x900")

        menubar = Menu(self.root)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_document)
        file_menu.add_command(label="Open", command=self.open_document)
        file_menu.add_command(label="Save", command=self.save_document)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

        self.blocks = []
        self.preview_image = None

        self.setup_ui()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg="lightgray")
        self.main_frame.pack(fill="both", expand=True)

        self.toolbar = tk.Frame(self.main_frame, height=40, bg="lightgray")
        self.toolbar.pack(side="top", fill="x")

        add_eq_button = tk.Button(self.toolbar, text="Add Equation", command=self.add_equation)
        add_eq_button.pack(side="left", padx=5, pady=5)
        add_frac_button = tk.Button(self.toolbar, text="Add Fraction", command=self.add_fraction)
        add_frac_button.pack(side="left", padx=5, pady=5)
        preview_button = tk.Button(self.toolbar, text="Preview LaTeX", command=self.preview_latex)
        preview_button.pack(side="left", padx=5, pady=5)

        self.editor_preview_frame = tk.Frame(self.main_frame, bg="lightgray")
        self.editor_preview_frame.pack(side="top", fill="both", expand=True)

        self.editor_page_frame = tk.Frame(self.editor_preview_frame, bg="white", bd=2, relief="ridge")
        self.editor_page_frame.pack(side="left", expand=True, padx=20, pady=20)
        self.editor_canvas = tk.Canvas(self.editor_page_frame, width=612, height=792, bg="white")
        self.editor_canvas.pack()

        self.preview_page_frame = tk.Frame(self.editor_preview_frame, bg="white", bd=2, relief="ridge")
        self.preview_page_frame.pack(side="left", expand=True, padx=20, pady=20)
        self.preview_canvas = tk.Canvas(self.preview_page_frame, width=612, height=792, bg="white")
        self.preview_canvas.pack()

    def new_document(self):
        self.blocks.clear()
        self.editor_canvas.delete("all")
        messagebox.showinfo("New", "Started a new document.")

    def open_document(self):
        messagebox.showinfo("Open", "Feature not yet implemented.")

    def save_document(self):
        messagebox.showinfo("Save", "Feature not yet implemented.")

    def add_equation(self):
        block = EquationBlock(self.editor_canvas, "x^2 + y^2 = z^2", font_size=10)
        block.widget.place(x=50, y=50)
        self.blocks.append(block)

    def add_fraction(self):
        block = FractionBlock(self.editor_canvas, "1", "2", font_size=10)
        block.widget.place(x=50, y=150)
        self.blocks.append(block)

    def gather_latex(self):
        if not self.blocks:
            return r"\mbox{}"
        lines = []
        lines.append(r"\setlength{\unitlength}{1pt}")
        lines.append(r"\begin{picture}(612,792)")
        for block in self.blocks:
            x = block.widget.winfo_x()
            y = block.widget.winfo_y()
            y_inverted = 792 - y
            block_latex = block.get_latex().strip()
            if block_latex:
                lines.append(fr"\put({x},{y_inverted}){{\makebox(0,0)[lt]{{{block_latex}}}}}")
        lines.append(r"\end{picture}")
        return "\n".join(lines)

    def compile_latex_to_pdf(self, latex_content):
        """
        Create a minimal LaTeX document with zero margins so the page is exactly 612×792 pt.
        Suppresses pdflatex output unless compilation fails.
        """
        document = rf"""\documentclass[letterpaper]{{article}}
\usepackage[paperwidth=612pt,paperheight=792pt,margin=0pt]{{geometry}}
\usepackage{{amsmath}}
\usepackage{{anyfontsize}}
\pagestyle{{empty}}
\begin{{document}}
{latex_content}
\end{{document}}
"""
        cwd = os.getcwd()
        tex_path = os.path.join(cwd, "preview.tex")
        pdf_path = os.path.join(cwd, "preview.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(document)

        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_path],
                cwd=cwd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            messagebox.showerror(
                "LaTeX Compilation Error",
                f"pdflatex failed. See preview.log in the working directory for details."
            )
            return None

        if not os.path.exists(pdf_path):
            messagebox.showerror("File Error", "PDF file was not generated.")
            return None

        return pdf_path


    def preview_latex(self):
        latex_content = self.gather_latex()
        pdf_file = self.compile_latex_to_pdf(latex_content)
        if pdf_file is None:
            return
        try:
            pages = convert_from_path(pdf_file, first_page=1, last_page=1)
            if pages:
                img = pages[0]
                img.thumbnail((612, 792))
                self.preview_image = ImageTk.PhotoImage(img)
                self.preview_canvas.delete("all")
                x_center = (612 - img.width) // 2
                y_center = (792 - img.height) // 2
                self.preview_canvas.create_image(x_center, y_center, anchor="nw", image=self.preview_image)
        except Exception as e:
            messagebox.showerror("Conversion Error", f"Failed to convert PDF to image:\n{e}")

    def new_document(self):
        self.blocks.clear()
        self.editor_canvas.delete("all")
        self.current_file = None

    def save_document(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("EZLaTeX Files","*.json"),("All Files","*.*")])
        if not path: return
        data = []
        for b in self.blocks:
            if isinstance(b, EquationBlock):
                data.append({"type":"equation","equation":b.equation,"x":b.widget.winfo_x(),"y":b.widget.winfo_y(),"font_size":b.font_size})
            else:
                data.append({"type":"fraction","numerator":b.numerator,"denominator":b.denominator,"x":b.widget.winfo_x(),"y":b.widget.winfo_y(),"font_size":b.font_size})
        with open(path,"w") as f:
            json.dump({"blocks":data},f)
        self.current_file = path

    def open_document(self):
        path = filedialog.askopenfilename(filetypes=[("EZLaTeX Files","*.json"),("All Files","*.*")])
        if not path: return
        with open(path) as f:
            obj = json.load(f)
        self.new_document()
        for entry in obj["blocks"]:
            if entry["type"]=="equation":
                blk = EquationBlock(self.editor_canvas, entry["equation"], entry["font_size"])
            else:
                blk = FractionBlock(self.editor_canvas, entry["numerator"], entry["denominator"], entry["font_size"])
            blk.widget.place(x=entry["x"], y=entry["y"])
            self.blocks.append(blk)
        self.current_file = path

if __name__ == "__main__":
    root = tk.Tk()
    editor = LaTeXEditor(root)
    root.mainloop()
