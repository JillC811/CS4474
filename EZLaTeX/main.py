import tkinter as tk
from editor import LaTeXEditor

if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')
    LaTeXEditor(root)
    root.mainloop()

