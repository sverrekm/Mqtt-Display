from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRect
from .resizable_widget import ResizableWidget

class GaugeWidget(ResizableWidget):
    def __init__(self, topic, mqtt_client=None, parent=None, config=None):
        super().__init__(config.get('type', 'gauge'), topic, mqtt_client, parent, config)
        self.value = 0.0
        self.init_content()
        self.connect_signals()
        self.apply_config()

    def init_content(self):
        """Initialize the content of the gauge widget."""
        # Main container for the gauge and its labels
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Create widgets
        self.title_label_internal = QLabel()
        self.title_label_internal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gauge_painter = GaugePainter(self)
        self.value_label = QLabel("0.0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add to layout
        self.layout.addWidget(self.title_label_internal)
        self.layout.addWidget(self.gauge_painter, 1) # Painter takes stretch
        self.layout.addWidget(self.value_label)

        self.content_layout.addWidget(container)

    def connect_signals(self):
        if self.mqtt_client:
            print(f"[DEBUG] GaugeWidget subscribing to topic: {self.topic}")
            self.mqtt_client.subscribe(self.topic)
            self.mqtt_client.message_received.connect(self.on_message_received)

    def on_message_received(self, topic, message):
        if topic == self.topic:
            try:
                print(f"[DEBUG] GaugeWidget received: topic={topic}, message={message}")
                self.value = float(message)
                self.value_label.setText(self.format_value(self.value))
                if self.error_state: self.clear_error()
                self.gauge_painter.update()
            except (ValueError, TypeError):
                self.show_error(f"Invalid payload: '{message}'")
            except RuntimeError:
                pass # Widget might be deleted

    def apply_config(self):
        super().apply_config()
        self.title_label.hide() # Hide ResizableWidget's title
        
        self.title_label_internal.setText(self.config.get('display_name', self.topic))
        self.value_label.setText(self.format_value(self.value))

        text_color = self.config.get('text_color', '#D9D9D9')
        font_size = int(self.config.get('font_size', 12))
        self.title_label_internal.setStyleSheet(f"color: {text_color}; font-size: {max(10, font_size - 2)}px; font-weight: bold;")
        self.value_label.setStyleSheet(f"color: {text_color}; font-size: {font_size}px;")

        self.gauge_painter.update()

    def get_value(self):
        return str(self.value)

class GaugePainter(QWidget):
    def __init__(self, parent_widget: GaugeWidget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            config = self.parent_widget.config
            value = self.parent_widget.value
            
            gauge_type = config.get('type', 'gauge')
            min_val = float(config.get('min_value', 0.0))
            max_val = float(config.get('max_value', 100.0))
            accent_color = config.get('accent_color', '#0d6efd')
            warning_color = self.parent_widget.get_warning_color(value)
            
            rect = self.rect()
            center = rect.center()

            if gauge_type == 'gauge_circular':
                self.draw_circular_gauge(painter, rect, center, value, min_val, max_val, accent_color, warning_color)
            elif gauge_type == 'gauge_linear':
                self.draw_linear_gauge(painter, rect, center, value, min_val, max_val, accent_color, warning_color)
            else:
                self.draw_arc_gauge(painter, rect, center, value, min_val, max_val, accent_color, warning_color)
        except Exception as e:
            print(f"[ERROR] Gauge paint event failed: {e}")
        finally:
            painter.end()

    def draw_arc_gauge(self, painter, rect, center, value, min_val, max_val, accent_color, warning_color):
        radius = min(rect.width(), rect.height()) / 2 - 5
        start_angle, span_angle = 210 * 16, 120 * 16
        painter.setPen(QPen(QColor(200, 200, 200, 50), 12))
        # Convert all float values to int for drawArc
        painter.drawArc(int(center.x() - radius), int(center.y() - radius), int(radius * 2), int(radius * 2), start_angle, span_angle)
        if max_val > min_val:
            normalized_value = max(0, min(1, (value - min_val) / (max_val - min_val)))
            value_angle = int(normalized_value * 120 * 16)
            arc_color = QColor(warning_color) if warning_color else QColor(accent_color)
            painter.setPen(QPen(arc_color, 12))
            painter.drawArc(int(center.x() - radius), int(center.y() - radius), int(radius * 2), int(radius * 2), start_angle, value_angle)

    def draw_circular_gauge(self, painter, rect, center, value, min_val, max_val, accent_color, warning_color):
        radius = min(rect.width(), rect.height()) / 2 - 10
        painter.setPen(QPen(QColor(200, 200, 200, 50), 8))
        painter.drawEllipse(int(center.x() - radius), int(center.y() - radius), int(radius * 2), int(radius * 2))
        if max_val > min_val:
            normalized_value = max(0, min(1, (value - min_val) / (max_val - min_val)))
            value_angle = int(normalized_value * 360 * 16)
            arc_color = QColor(warning_color) if warning_color else QColor(accent_color)
            painter.setPen(QPen(arc_color, 8))
            painter.drawArc(int(center.x() - radius), int(center.y() - radius), int(radius * 2), int(radius * 2), 90 * 16, -value_angle)

    def draw_linear_gauge(self, painter, rect, center, value, min_val, max_val, accent_color, warning_color):
        bar_height, bar_width, bar_x = max(15, min(rect.height() - 10, 30)), rect.width() - 20, 10
        bar_y = center.y() - bar_height / 2
        painter.setBrush(QBrush(QColor(200, 200, 200, 50)))
        painter.setPen(Qt.PenStyle.NoPen)
        # Convert float values to int for drawRoundedRect
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(bar_width), int(bar_height), bar_height/2, bar_height/2)
        if max_val > min_val:
            normalized_value = max(0, min(1, (value - min_val) / (max_val - min_val)))
            value_width = int(normalized_value * bar_width)
            bar_color = QColor(warning_color) if warning_color else QColor(accent_color)
            painter.setBrush(QBrush(bar_color))
            painter.drawRoundedRect(int(bar_x), int(bar_y), int(value_width), int(bar_height), bar_height/2, bar_height/2)