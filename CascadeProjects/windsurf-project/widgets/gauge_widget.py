from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QConicalGradient
import math
from .base_widget import BaseWidget

class GaugeWidget(BaseWidget):
    def __init__(self, topic, min_val=0, max_val=100, initial_val=0, parent=None):
        super().__init__("gauge", topic, parent)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.value = float(initial_val)
        
        # Set minimum size
        self.setMinimumSize(120, 80)
        
        # Create value label
        self.value_label = QLabel(str(initial_val))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 16px;
                color: #212529;
            }
        """)
        
        # Add to layout
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(self.value_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addStretch(1)
    
    def paintEvent(self, event):
        """Draw the gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        size = min(width, height * 1.5)
        x = (width - size) // 2
        y = 0
        
        # Draw the gauge background
        pen = QPen(QColor(200, 200, 200), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw the gauge arc (semi-circle)
        rect = QRectF(x, y, size, size * 2)
        start_angle = 180 * 16  # 180 degrees in 1/16th of a degree
        span_angle = 180 * 16   # 180 degrees in 1/16th of a degree
        painter.drawArc(rect, start_angle, span_angle)
        
        # Calculate the angle for the value
        value_range = self.max_val - self.min_val
        if value_range > 0:
            ratio = (self.value - self.min_val) / value_range
            ratio = max(0, min(1, ratio))  # Clamp between 0 and 1
            angle = 180 * ratio  # 0-180 degrees
            
            # Draw the value arc with a gradient
            gradient = QConicalGradient(rect.center(), 180)  # 180 degrees is at the top
            gradient.setColorAt(0, QColor(255, 0, 0))      # Red at min
            gradient.setColorAt(0.5, QColor(255, 255, 0))  # Yellow at middle
            gradient.setColorAt(1, QColor(0, 255, 0))      # Green at max
            
            pen = QPen(gradient, 6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            # Draw the value arc
            painter.drawArc(rect, start_angle, int(span_angle * ratio))
        
        # Draw the needle
        if value_range > 0:
            radius = size // 2 - 10
            center = QPointF(x + size // 2, size)
            angle_rad = math.radians(180 - (180 * ratio))
            end_x = center.x() + radius * math.cos(angle_rad)
            end_y = center.y() - radius * math.sin(angle_rad)
            
            pen = QPen(QColor(50, 50, 50), 2)
            painter.setPen(pen)
            painter.drawLine(center, QPointF(end_x, end_y))
            
            # Draw center circle
            painter.setBrush(QBrush(QColor(50, 50, 50)))
            painter.drawEllipse(center, 5, 5)
    
    def on_message_received(self, topic, message):
        """Handle incoming MQTT messages"""
        if topic == self.topic:
            try:
                self.set_value(float(message))
            except (ValueError, TypeError):
                pass
    
    def set_value(self, value):
        """Set the gauge value and update the display"""
        try:
            self.value = float(value)
            self.value_label.setText(f"{self.value:.1f}")
            self.update()  # Trigger a repaint
        except (ValueError, TypeError):
            pass
    
    def get_value(self):
        """Return the current gauge value"""
        return self.value
    
    def resizeEvent(self, event):
        """Handle widget resize events"""
        self.update()  # Redraw the gauge when resized
