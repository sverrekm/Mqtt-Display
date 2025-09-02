from PyQt6.QtWidgets import QPushButton
from .base_widget import BaseWidget

class ButtonWidget(BaseWidget):
    def __init__(self, topic, label="Toggle", parent=None):
        super().__init__("button", topic, parent)
        self.state = False
        
        # Create button with styling
        self.button = QPushButton(label)
        self.button.setCheckable(True)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 30px;
                font-weight: 500;
            }
            QPushButton:checked {
                background-color: #0d6efd;
                color: white;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:checked:hover {
                background-color: #0b5ed7;
            }
        """)
        
        # Connect signals
        self.button.clicked.connect(self.on_click)
        
        # Add button to layout with stretch to center it
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(self.button, 0, QPushButton.AlignmentFlag.AlignCenter)
        self.content_layout.addStretch(1)
    
    def on_click(self):
        """Handle button click"""
        self.state = self.button.isChecked()
        self.button.setText("ON" if self.state else "OFF")
    
    def get_value(self):
        """Return the current state of the button"""
        return "ON" if self.state else "OFF"
    
    def set_value(self, value):
        """Set the button state"""
        if isinstance(value, bool):
            self.state = value
        else:
            self.state = str(value).lower() in ('true', 'on', '1')
        self.button.setChecked(self.state)
        self.button.setText("ON" if self.state else "OFF")
