from PyQt6.QtWidgets import QLabel
from .base_widget import BaseWidget

class LabelWidget(BaseWidget):
    def __init__(self, topic, initial_value="", parent=None):
        super().__init__("label", topic, parent)
        self.value_label = QLabel(initial_value)
        self.value_label.setAlignment(QLabel.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.value_label, 1)  # Add stretch to center vertically
        
        # Set font size based on widget size
        font = self.value_label.font()
        font.setPointSize(12)
        self.value_label.setFont(font)
        
        # Set style
        self.value_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-weight: 500;
            }
        """)
    
    def on_message_received(self, topic, message):
        """Handle incoming MQTT messages"""
        if topic == self.topic:
            self.value_label.setText(str(message))
    
    def get_value(self):
        """Return the current value of the widget"""
        return self.value_label.text()
