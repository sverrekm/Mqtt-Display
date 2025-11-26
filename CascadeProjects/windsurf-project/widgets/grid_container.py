from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen

class GridContainer(QWidget):
    def __init__(self, grid_size=20, parent=None):
        super().__init__(parent)
        self.grid_size = grid_size
        self.show_grid = True

        # Set object name for CSS selector
        self.setObjectName("grid_container")

        # Set transparent attributes for presentation mode
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        """Draw grid overlay with transparent background support"""
        # DO NOT call super().paintEvent() - it fills with default widget background

        painter = QPainter(self)

        # Fill with fully transparent first (critical for presentation mode)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 0))

        if not self.show_grid:
            return

        # Draw grid on top if enabled
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set grid pen
        pen = QPen(QColor(220, 220, 220, 100), 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        # Draw vertical lines
        width = self.width()
        height = self.height()

        for x in range(0, width, self.grid_size):
            painter.drawLine(x, 0, x, height)

        # Draw horizontal lines
        for y in range(0, height, self.grid_size):
            painter.drawLine(0, y, width, y)
    
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid = not self.show_grid
        self.update()
