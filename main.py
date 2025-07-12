import sys
import os
import base64
import io
from PyQt5 import QtWidgets, QtCore, QtGui
from PIL import ImageGrab, Image
import requests
import pyperclip

MATHPIX_APP_ID = os.getenv("MATHPIX_APP_ID")
MATHPIX_APP_KEY = os.getenv("MATHPIX_APP_KEY")

def mathpix_ocr(image):
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
    r = requests.post("https://api.mathpix.com/v3/text", json=data, headers=headers)
    try:
        return r.json().get("latex_simplified", "")
    except:
        return ""

class SnippingWidget(QtWidgets.QWidget):
    snip_complete = QtCore.pyqtSignal(Image.Image)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setWindowState(self.windowState() | QtCore.Qt.WindowFullScreen)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.setCursor(QtCore.Qt.CrossCursor)

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor("red"), 2))
        qp.drawRect(QtCore.QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        x1, y1 = self.begin.x(), self.begin.y()
        x2, y2 = self.end.x(), self.end.y()
        x_min, y_min = min(x1, x2), min(y1, y2)
        x_max, y_max = max(x1, x2), max(y1, y2)
        self.hide()
        img = ImageGrab.grab(bbox=(x_min, y_min, x_max, y_max))
        self.snip_complete.emit(img)

class FormulaPopup(QtWidgets.QWidget):
    def __init__(self, latex_text):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setWindowTitle("Extracted Formula (LaTeX)")
        self.resize(500, 200)
        layout = QtWidgets.QVBoxLayout()
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setText(latex_text)
        layout.addWidget(self.text_edit)
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
        pyperclip.copy(self.text_edit.toPlainText())

def main():
    app = QtWidgets.QApplication(sys.argv)

    def on_snip_complete(image):
        latex = mathpix_ocr(image)
        popup = FormulaPopup(latex)
        popup.show()

    snipper = SnippingWidget()
    snipper.snip_complete.connect(on_snip_complete)
    snipper.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()