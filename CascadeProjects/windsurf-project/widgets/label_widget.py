from PyQt6.QtWidgets import QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from .resizable_widget import ResizableWidget
from pathlib import Path

class LabelWidget(ResizableWidget):
    def __init__(self, topic, mqtt_client=None, parent=None, config=None):
        super().__init__("label", topic, mqtt_client, parent, config)
        self.init_content()
        self.connect_signals()
        self.apply_config()

    def init_content(self):
        """Initialize the content of the label widget."""
        # Create horizontal layout for icon + value
        content_container = QHBoxLayout()
        content_container.setSpacing(4)
        content_container.setContentsMargins(0, 0, 0, 0)

        # Icon label (left position)
        self.icon_label_left = QLabel()
        self.icon_label_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label_left.hide()

        # Value label
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon label (right position)
        self.icon_label_right = QLabel()
        self.icon_label_right.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label_right.hide()

        content_container.addWidget(self.icon_label_left)
        content_container.addWidget(self.value_label, 1)  # Value label gets stretch
        content_container.addWidget(self.icon_label_right)

        self.content_layout.addLayout(content_container)

    def connect_signals(self):
        """Connect MQTT signals."""
        if self.mqtt_client:
            print(f"[DEBUG] LabelWidget subscribing to topic: {self.topic}")
            self.mqtt_client.subscribe(self.topic)
            self.mqtt_client.message_received.connect(self.on_message_received)

    def on_message_received(self, topic, message):
        """Handle incoming MQTT messages"""
        if topic == self.topic:
            try:
                print(f"[DEBUG] LabelWidget received: topic={topic}, message={message}")
                formatted_value = self.format_value(message)
                self.value_label.setText(formatted_value)
                if self.error_state:
                    self.clear_error()
            except Exception as e:
                self.show_error(f"Failed to display value: {e}")

    def apply_config(self):
        """Apply configuration to the widget."""
        super().apply_config()

        text_color = self.config.get('text_color', '#D9D9D9')
        font_size = int(self.config.get('font_size', 16))
        self.value_label.setStyleSheet(f"color: {text_color}; font-size: {font_size}px; font-weight: bold;")

        # Show/hide value label based on config
        show_text = self.config.get('show_text', True)
        if show_text:
            self.value_label.show()
        else:
            self.value_label.hide()

        # Update icon display for left/right positions
        self._update_content_icon()

    def _update_content_icon(self):
        """Update icon display for left/right positions"""
        icon_data = self.config.get('icon_data', '')
        is_text = self.config.get('icon_is_text', False)
        icon_size = self.config.get('icon_size', 24)
        icon_position = self.config.get('icon_position', 'left')

        # Hide both icons first
        self.icon_label_left.hide()
        self.icon_label_right.hide()

        if not icon_data or icon_position not in ['left', 'right']:
            return

        # Determine which label to use
        icon_label = self.icon_label_left if icon_position == 'left' else self.icon_label_right

        # Set icon content
        if is_text:
            # Text/emoji icon
            icon_label.setPixmap(QPixmap())
            icon_label.setText(icon_data)
            text_color = self.config.get('text_color', '#D9D9D9')
            icon_label.setStyleSheet(f"""
                QLabel {{
                    color: {text_color};
                    font-size: {icon_size}px;
                    background: transparent;
                    border: none;
                    padding: 2px;
                }}
            """)
        else:
            # Image icon
            icon_label.setText("")
            if Path(icon_data).exists():
                pixmap = QPixmap(icon_data)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        icon_size, icon_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    icon_label.setPixmap(scaled)
                    icon_label.setStyleSheet("background: transparent; border: none; padding: 2px;")

        icon_label.show()

    def get_value(self):
        """Return the current value of the widget"""
        return self.value_label.text()
