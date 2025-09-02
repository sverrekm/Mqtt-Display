from PyQt6.QtWidgets import QSlider, QLabel
from PyQt6.QtCore import Qt
from .base_widget import BaseWidget

class SliderWidget(BaseWidget):
    def __init__(self, topic, min_val=0, max_val=100, initial_val=0, parent=None):
        super().__init__("slider", topic, parent)
        from PyQt6.QtWidgets import QSlider
        
        # Create slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(initial_val)
        
        # Create value display
        self.value_label = QLabel(str(initial_val))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Style the slider and label
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ced4da;
                height: 8px;
                background: #e9ecef;
                margin: 0px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0d6efd;
                border: 1px solid #0a58ca;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #0b5ed7;
            }
        """)
        
        self.value_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                color: #212529;
                font-size: 12px;
            }
        """)
        
        # Connect signals
        self.slider.valueChanged.connect(self.on_value_changed)
        
        # Add to layout with proper spacing
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(self.value_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.slider)
        self.content_layout.addStretch(1)
    
    def on_value_changed(self, value):
        """Handle slider value changes"""
        self.value_label.setText(str(value))
    
    def get_value(self):
        """Return the current slider value"""
        return self.slider.value()
    
    def set_value(self, value):
        """Set the slider value"""
        try:
            self.slider.setValue(int(float(value)))
        except (ValueError, TypeError):
            pass
