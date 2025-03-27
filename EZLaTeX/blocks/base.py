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
        # Set a red border and change cursor to a hand pointer.
        self.widget.config(highlightthickness=2, highlightbackground="red", cursor="hand2")
        self.widget.bind("<Button-1>", self.on_click)
        self.widget.bind("<B1-Motion>", self.on_drag)
        self.widget.bind("<ButtonRelease-1>", self.on_release)
        self.offset_x = self.offset_y = 0
        self.dragged = False

    def on_click(self, e):
        self.offset_x, self.offset_y = e.x, e.y
        self.dragged = False

    def on_drag(self, e):
        self.dragged = True
        new_x = self.widget.winfo_x() + e.x - self.offset_x
        new_y = self.widget.winfo_y() + e.y - self.offset_y

        pw, ph = self.master.winfo_width(), self.master.winfo_height()
        ww, wh = self.widget.winfo_width(), self.widget.winfo_height()
        new_x = max(0, min(new_x, pw - ww))
        new_y = max(0, min(new_y, ph - wh))

        snapped_to = None
        for other in self.master.editor.blocks:
            if other is self:
                continue
            ox = other.widget.winfo_x()
            oy = other.widget.winfo_y()
            ow = other.widget.winfo_width()
            if abs(new_x - (ox + ow)) < SNAP_DISTANCE and abs(new_y - oy) < VERTICAL_THRESHOLD:
                occupied = False
                for b in self.master.editor.blocks:
                    if b is self or b is other:
                        continue
                    bx = b.widget.winfo_x()
                    by = b.widget.winfo_y()
                    if abs(bx - (ox + ow)) < 2 and abs(by - oy) < 2:
                        occupied = True
                        break
                if not occupied:
                    new_x, new_y = ox + ow, oy
                    snapped_to = other
                    break
            elif abs((new_x + ww) - ox) < SNAP_DISTANCE and abs(new_y - oy) < VERTICAL_THRESHOLD:
                occupied = False
                for b in self.master.editor.blocks:
                    if b is self or b is other:
                        continue
                    bx = b.widget.winfo_x()
                    by = b.widget.winfo_y()
                    if abs(bx - (ox - ww)) < 2 and abs(by - oy) < VERTICAL_THRESHOLD:
                        occupied = True
                        break
                if not occupied:
                    new_x, new_y = ox - ww, oy
                    snapped_to = other
                    break

        self.widget.place(x=new_x, y=new_y)
        if snapped_to is not None:
            self.font_size = snapped_to.font_size
            self.update_display()
        self.master.editor.update_group_borders()

    def on_release(self, e):
        if not self.dragged:
            self.edit(e)

    def get_latex(self):
        return ""

    def edit(self, event):
        pass
