from PyQt6.QtWidgets import QSlider, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from .resizable_widget import ResizableWidget

class SliderWidget(ResizableWidget):
    def __init__(self, topic, mqtt_client=None, parent=None, config=None):
        super().__init__("slider", topic, mqtt_client, parent, config)
        self.init_content()
        self.connect_signals()
        self.apply_config()
        
    def init_content(self):
        """Initialize the content of the slider widget."""
        self.slider = QSlider()
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add to layout
        self.content_layout.addWidget(self.value_label)
        self.content_layout.addWidget(self.slider)

    def connect_signals(self):
        if self.mqtt_client:
            print(f"[DEBUG] SliderWidget subscribing to topic: {self.topic}")
            self.mqtt_client.subscribe(self.topic)
            self.mqtt_client.message_received.connect(self.on_message_received)
        self.slider.valueChanged.connect(self.on_slider_changed)

    def on_slider_changed(self, value):
        self.value_label.setText(str(value))
        if self.mqtt_client and self.mqtt_client.connected:
            self.mqtt_client.publish(self.topic, str(value))

    def on_message_received(self, topic, message):
        if topic == self.topic:
            try:
                print(f"[DEBUG] SliderWidget received: topic={topic}, message={message}")
                self.slider.blockSignals(True)
                value = int(float(message))
                min_val, max_val = self.slider.minimum(), self.slider.maximum()
                clamped_value = max(min_val, min(max_val, value))
                self.slider.setValue(clamped_value)
                self.value_label.setText(str(clamped_value))
                if self.error_state: self.clear_error()
            except (ValueError, TypeError):
                self.show_error(f"Invalid payload: '{message}'")
            except RuntimeError:
                pass # Widget might be deleted
            finally:
                if self.slider and self.slider.signalsBlocked():
                    self.slider.blockSignals(False)

    def apply_config(self):
        """Apply configuration to the widget."""
        super().apply_config()
        
        min_v = int(self.config.get('min_value', 0))
        max_v = int(self.config.get('max_value', 100))
        
        self.slider.blockSignals(True)
        self.slider.setMinimum(min_v)
        self.slider.setMaximum(max_v)
        self.slider.blockSignals(False)
        
        orientation = Qt.Orientation.Vertical if self.config.get('slider_orientation') == 'vertical' else Qt.Orientation.Horizontal
        self.slider.setOrientation(orientation)
        
        accent_color = self.config.get('accent_color', '#0d6efd')
        stylesheet = ""
        if orientation == Qt.Orientation.Horizontal:
            stylesheet = f"""
                QSlider::groove:horizontal {{ border: 1px solid #ced4da; height: 8px; background: #e9ecef; margin: 0px; border-radius: 4px; }}
                QSlider::handle:horizontal {{ background: {accent_color}; border: 1px solid {accent_color}; width: 16px; margin: -4px 0; border-radius: 8px; }}
            """
        else:
            stylesheet = f"""
                QSlider::groove:vertical {{ border: 1px solid #ced4da; width: 8px; background: #e9ecef; margin: 0px; border-radius: 4px; }}
                QSlider::handle:vertical {{ background: {accent_color}; border: 1px solid {accent_color}; height: 16px; margin: 0 -4px; border-radius: 8px; }}
            """
        self.slider.setStyleSheet(stylesheet)
        
        text_color = self.config.get('text_color', '#D9D9D9')
        font_size = int(self.config.get('font_size', 12))
        self.value_label.setStyleSheet(f"color: {text_color}; font-size: {font_size}px;")

    def get_value(self):
        return str(self.slider.value())