from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent, QPainter, QColor

class BaseWidget(QFrame):
    """Base class for all dashboard widgets"""
    
    def __init__(self, widget_type, topic, parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.topic = topic
        self.dragging = False
        self.drag_position = QPoint()
        
        # Set up the widget
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setMinimumSize(100, 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Main layout with margins
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)
        
        # Add title bar
        self.title_bar = QLabel(f"{widget_type}: {topic}")
        self.title_bar.setStyleSheet("""
            background-color: #e0e0e0; 
            padding: 2px 5px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 10px;
        """)
        self.title_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_bar)
        
        # Content area
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(2, 2, 2, 2)
        self.content_layout.setSpacing(2)
        self.layout.addWidget(self.content, 1)  # Add stretch factor to push content to top
        
        # Set up event filter for hover effects
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < 30:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
            
    def get_value(self):
        """Return the current value of the widget"""
        raise NotImplementedError("Subclasses must implement get_value()")
