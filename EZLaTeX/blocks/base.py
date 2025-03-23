import tkinter as tk

DISPLAY_FONT_SCALE = 0.85
STANDARD_FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36]
MODAL_OFFSET = 10
SNAP_DISTANCE = 10
VERTICAL_THRESHOLD = 10


class Block:
    def __init__(self, master, text="Block", font_size=10):
        self.master, self.text, self.font_size = master, text, font_size
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
        new_x = max(0, min(new_x, pw - ww))
        new_y = max(0, min(new_y, ph - wh))

        for other in self.master.editor.blocks:
            if other is self:
                continue
            ox, oy = other.widget.winfo_x(), other.widget.winfo_y()
            ow = other.widget.winfo_width()

            if abs(new_x - (ox + ow)) < SNAP_DISTANCE and abs(new_y - oy) < VERTICAL_THRESHOLD:
                new_x, new_y = ox + ow, oy
            elif abs((new_x + ww) - ox) < SNAP_DISTANCE and abs(new_y - oy) < VERTICAL_THRESHOLD:
                new_x, new_y = ox - ww, oy

        self.widget.place(x=new_x, y=new_y)


    def get_latex(self):
        return ""

    def edit(self, event):
        pass
