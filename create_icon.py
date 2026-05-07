"""Create a simple icon for TranslateTor."""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QRect
import sys

def create_icon():
    app = QApplication(sys.argv)

    # Create 256x256 icon
    size = 256
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(30, 30, 30))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw background circle
    painter.setPen(QPen(QColor(100, 100, 255), 8))
    painter.setBrush(QColor(40, 40, 80))
    painter.drawEllipse(20, 20, size-40, size-40)

    # Draw "T" letter
    font = QFont("Arial", 120, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "T")

    # Draw translation arrows
    painter.setPen(QPen(QColor(100, 255, 100), 6))
    # Left arrow
    painter.drawLine(60, 180, 100, 180)
    painter.drawLine(90, 170, 100, 180)
    painter.drawLine(90, 190, 100, 180)
    # Right arrow
    painter.drawLine(156, 180, 196, 180)
    painter.drawLine(166, 170, 156, 180)
    painter.drawLine(166, 190, 156, 180)

    painter.end()

    # Save icon
    pixmap.save("resources/icon.png", "PNG")
    print("Icon created: resources/icon.png")

if __name__ == "__main__":
    create_icon()
