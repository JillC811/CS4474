# CS4474

# EzTeX

**EzTeX** is a modular, block-based LaTeX editor designed specifically for Ontario High School Math. It provides an intuitive graphical interface that lets educators and students construct complex mathematical expressions using draggable, editable blocks. You can preview the final LaTeX rendering in real time and export it as a PDF.

---

## Features

- **Block-Based Editing:**  
  Create and arrange blocks for exponents, fractions, nth roots, operations (including summation, product, integral, logarithm, and more).

- **Snap & Group:**  
  Drag blocks that automatically snap together, with automatic font size propagation and a visual blue border highlighting grouped blocks.

- **Real-Time Preview:**  
  Compile your LaTeX code using `pdflatex` (via MikTeX) and preview it on the fly.

- **Export Options:**  
  View the raw LaTeX code or export the rendered document as a PDF.

---

## Prerequisites

### Python

EzTeX requires **Python 3.x**. It is recommended to use Python 3.8 or later.

### Python Packages

Install the required Python packages with:

```bash
pip install pillow pdf2image
```


### MikTeX

**Important:** EzTeX relies on `pdflatex` for LaTeX compilation. You must have [MikTeX](https://miktex.org/download) installed on your system and ensure that `pdflatex` is available in your system PATH.

1. **Download MikTeX:**  
   Go to [https://miktex.org/download](https://miktex.org/download) and download the installer for your operating system.

2. **Install MikTeX:**  
   Follow the installation instructions. Be sure to enable the option to install missing packages on the fly.

3. **Verify Installation:**  
   Open a terminal or command prompt and run:

   ```bash
   pdflatex --version
   ```
This should display version information, confirming that MikTeX is correctly installed.

---

## Installation

Clone the repository and navigate into the project directory:

```bash
git clone <repository-url>
cd EzTeX
```

## Usage

To launch EzTeX, run:

```bash
python main.py
```
Or open the EzTex folder in VSCode and run from there.

The application will open in a maximized window. Use the toolbar to add blocks and build your mathematical expressions. You can:

- **Drag & Snap:** Rearrange blocks on the editor canvas; snapped groups are highlighted with a blue border.
- **Edit Blocks:** Single-click any block to edit its contents.
- **Preview LaTeX:** Click "Preview LaTeX" to see the rendered output.
- **View Code:** Click "View Code" to see the generated LaTeX source.
- **Export PDF:** Save your rendered document as a PDF.

---

## Troubleshooting

- **MikTeX Issues:**  
  Ensure MikTeX is properly installed and `pdflatex` is in your system PATH.
  
- **Python Errors:**  
  Verify that you have all required dependencies installed (`pillow`, `pdf2image`).

---
