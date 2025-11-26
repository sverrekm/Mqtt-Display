from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QAbstractButton
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush
from .resizable_widget import ResizableWidget

class AnimatedToggle(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumSize(48, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._handle_position = 0.0
        self.animation = QPropertyAnimation(self, b"handlePosition", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)
        self.toggled.connect(self._animate_toggle)

    @pyqtProperty(float)
    def handlePosition(self):
        return self._handle_position

    @handlePosition.setter
    def handlePosition(self, pos):
        self._handle_position = pos
        self.update()

    def set_colors(self, on_color, off_color, handle_color):
        self._on_color = QColor(on_color)
        self._off_color = QColor(off_color)
        self._handle_color = QColor(handle_color)
        self.update()

    def _animate_toggle(self, checked):
        self.animation.setEndValue(1.0 if checked else 0.0)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track_color = self._on_color if self.isChecked() else self._off_color
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), self.height() / 2, self.height() / 2)
        handle_radius = (self.height() - 4) / 2
        handle_x = 2 + handle_radius + (self.width() - 4 - 2 * handle_radius) * self._handle_position
        painter.setBrush(QBrush(self._handle_color))
        painter.drawEllipse(QRectF(handle_x - handle_radius, self.height() / 2 - handle_radius, handle_radius * 2, handle_radius * 2))

class ToggleWidget(ResizableWidget):
    def __init__(self, topic, mqtt_client=None, parent=None, config=None):
        super().__init__("toggle", topic, mqtt_client, parent, config)
        self.init_content()
        self.connect_signals()
        self.apply_config()

    def init_content(self):
        container = QWidget()
        self.layout = QHBoxLayout(container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.toggle_label = QLabel()
        self.toggle_switch = AnimatedToggle()
        self.layout.addWidget(self.toggle_label)
        self.layout.addStretch()
        self.layout.addWidget(self.toggle_switch)
        self.content_layout.addWidget(container)

    def connect_signals(self):
        self.toggle_switch.toggled.connect(self.on_toggled)
        if self.mqtt_client:
            input_topic = self.config.get('toggle_input_topic', '').strip()
            if input_topic:
                self.mqtt_client.subscribe(input_topic)
                self.mqtt_client.message_received.connect(self.on_message_received)

    def on_toggled(self, checked):
        try:
            payload = self.config.get('toggle_on_payload', '1') if checked else self.config.get('toggle_off_payload', '0')
            if self.mqtt_client and self.mqtt_client.connected:
                self.mqtt_client.publish(self.topic, payload)
                if self.error_state: self.clear_error()
            elif not self.mqtt_client or not self.mqtt_client.connected:
                raise Exception("MQTT client not connected")
        except Exception as e:
            self.show_error(f"Publish failed: {e}")

    def on_message_received(self, topic, message):
        input_topic = self.config.get('toggle_input_topic', '').strip()
        if topic == input_topic:
            try:
                is_on = str(message).strip() == self.config.get('toggle_on_payload', '1')
                self.toggle_switch.blockSignals(True)
                self.toggle_switch.setChecked(is_on)
                if self.error_state: self.clear_error()
            except RuntimeError:
                pass # Widget might be deleted
            finally:
                if self.toggle_switch and self.toggle_switch.signalsBlocked():
                    self.toggle_switch.blockSignals(False)

    def apply_config(self):
        super().apply_config()
        self.toggle_label.setText(self.config.get('display_name', self.topic))
        
        on_color = self.config.get('accent_color', '#0d6efd')
        off_color = self.config.get('toggle_off_color', '#6c757d')
        handle_color = self.config.get('toggle_handle_color', '#ffffff')
        self.toggle_switch.set_colors(on_color, off_color, handle_color)
        
        text_color = self.config.get('text_color', '#D9D9D9')
        font_size = int(self.config.get('font_size', 12))
        self.toggle_label.setStyleSheet(f"color: {text_color}; font-size: {font_size}px;")

    def get_value(self):
        return str(self.toggle_switch.isChecked())