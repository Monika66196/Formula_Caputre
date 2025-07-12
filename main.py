A lightweight PyQt5-based floating app that allows users to snip a portion of their screen 
(containing a mathematical formula), send it to the Mathpix OCR API, and display the extracted 
LaTeX formula in a popup window.

Features:
- Floating screen capture tool
- OCR via Mathpix API
- LaTeX formula preview
- Copy and edit functionality

Author: Your Name
License: MIT
"""

import sys
import os
import base64
import io
from PyQt5 import QtWidgets, QtCore, QtGui
from PIL import ImageGrab, Image
import requests
import pyperclip

# Load your Mathpix API credentials from environment variables
MATHPIX_APP_ID = os.getenv("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.getenv("MATHPIX_APP_KEY")

def mathpix_ocr(image):
    """
    Convert an image to LaTeX using Mathpix OCR API.
    Args:
        image (PIL.Image): Snipped screenshot containing a formula.
    Returns:
        str: LaTeX representation of the formula.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    headers = {
        "app_id": MATHPIX_APP_ID,
        "app_key": MATHPIX_APP_KEY,
        "Content-type": "application/json"
    }

    data = {
        "src": f"data:image/png;base64,{img_str}",
        "formats": ["latex_simplified"],
        "ocr": ["math", "text"]
    }

    try:
        response = requests.post("https://api.mathpix.com/v3/text", json=data, headers=headers)
        return response.json().get("latex_simplified", "")
    except Exception as e:
        print(f"Error calling Mathpix API: {e}")
        return ""

class SnippingWidget(QtWidgets.QWidget):
    """
    A fullscreen transparent widget for selecting a rectangular area of the screen.
    Emits a signal with the cropped image when the mouse is released.
    """
    snip_complete = QtCore.pyqtSignal(Image.Image)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setWindowState(self.windowState() | QtCore.Qt.WindowFullScreen)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(QtGui.QColor("red"), 2))
        painter.drawRect(QtCore.QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        # Capture the selected region
        x1, y1 = self.begin.x(), self.begin.y()
        x2, y2 = self.end.x(), self.end.y()
        x_min, y_min = min(x1, x2), min(y1, y2)
        x_max, y_max = max(x1, x2), max(y1, y2)

        self.hide()
        img = ImageGrab.grab(bbox=(x_min, y_min, x_max, y_max))
        self.snip_complete.emit(img)

class FormulaPopup(QtWidgets.QWidget):
    """
    A small popup window that displays the extracted LaTeX formula.
    Includes options to edit or copy the formula.
    """
    def __init__(self, latex_text):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setWindowTitle("Extracted Formula (LaTeX)")
        self.resize(500, 200)

        layout = QtWidgets.QVBoxLayout()

        # Text area to display LaTeX
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setText(latex_text)
        layout.addWidget(self.text_edit)

        # Buttons
        hbox = QtWidgets.QHBoxLayout()
        copy_btn = QtWidgets.QPushButton("Copy")
        copy_btn.clicked.connect(self.copy_text)
        hbox.addWidget(copy_btn)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        hbox.addWidget(close_btn)

        layout.addLayout(hbox)
        self.setLayout(layout)

    def copy_text(self):
        """
        Copy the LaTeX formula to clipboard.
        """
        pyperclip.copy(self.text_edit.toPlainText())

def main():
    app = QtWidgets.QApplication(sys.argv)

    def on_snip_complete(image):
        # When screenshot is done, send to OCR and show the result
        latex = mathpix_ocr(image)
        popup = FormulaPopup(latex)
        popup.show()

    snipper = SnippingWidget()
    snipper.snip_complete.connect(on_snip_complete)
    snipper.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
