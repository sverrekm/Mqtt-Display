from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                           QPushButton, QScrollArea, QFrame, QSizePolicy,
                           QComboBox, QLineEdit, QMessageBox, QInputDialog,
                           QMenu, QMenuBar, QFileDialog, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QMimeData, QRect
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor, QAction, QFont, QPen, QBrush, QConicalGradient
import json
import os
import math

# Import widget classes
from .grid_container import GridContainer

class Dashboard(QWidget):
    def __init__(self, mqtt_client, parent=None):
        super().__init__(parent)
        self.mqtt = mqtt_client
        self.widgets = []
        self.subscribed_topics = set()
        self.current_layout_file = None
        self.grid_size = 20
        self.show_grid = True
        self.presentation_mode = False
        self.setAcceptDrops(True)
        self.setAutoFillBackground(True)
        
        # Create main container without grid layout - use absolute positioning
        self.container = GridContainer(self.grid_size)
        self.container.setMinimumSize(1200, 800)
        
        # Create a scroll area for the dashboard
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.container)
        
        # Add the scroll area to the main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll)
        
        # Auto-load layout if specified in settings
        if hasattr(parent, 'settings') and 'layout_file' in parent.settings:
            self.load_layout(parent.settings['layout_file'])
            
        # Set up context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def init_ui(self):
        """Initialize the widget's UI elements"""
        # Set default style
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QFrame:hover {
                border: 1px solid #6c757d;
            }
        """)
        
    def show_add_widget_dialog(self):
        """Show dialog to add a new widget"""
        dialog = AddWidgetDialog(self)
        if dialog.exec():
            widget_type = dialog.get_selected_widget()
            topic = dialog.get_topic()
            if widget_type and topic:
                self.add_widget(widget_type, topic)
    
    def add_widget(self, widget_type, topic, x=None, y=None, **kwargs):
        """Add a widget to the dashboard
        
        Args:
            widget_type: Type of widget to add ('label', 'button', 'slider', 'gauge')
            topic: MQTT topic to subscribe to
            x: X-coordinate of the widget position (optional, will find next available if not specified)
            y: Y-coordinate of the widget position (optional, will find next available if not specified)
            **kwargs: Additional arguments for the widget constructor
            
        Returns:
            The created widget or None if creation failed
        """
        print(f"[DEBUG] Adding widget: type={widget_type}, topic={topic}, x={x}, y={y}, kwargs={kwargs}")
        try:
            # Import the resizable widget
            from .resizable_widget import ResizableWidget
            
            # Create the widget based on type using ResizableWidget as base
            print(f"[DEBUG] Creating resizable widget of type: {widget_type}")
            widget = ResizableWidget(widget_type, topic, mqtt_client=self.mqtt, parent=self.container)
            
            # Add specific content based on widget type
            if widget_type == 'label':
                from PyQt6.QtWidgets import QLabel
                from PyQt6.QtCore import Qt
                content = QLabel("0")
                content.setAlignment(Qt.AlignmentFlag.AlignCenter)
                widget.content_layout.addWidget(content)
                widget.value_widget = content
                
                def on_message_received(topic_msg, message):
                    if topic_msg == topic:
                        # Use widget's format_value method for proper formatting
                        formatted_value = widget.format_value(message)
                        content.setText(formatted_value)
                        
                        # Apply warning colors if enabled
                        warning_color = widget.get_warning_color(message)
                        if warning_color:
                            content.setStyleSheet(f"color: {warning_color}; font-weight: bold;")
                        else:
                            # Use configured text color
                            text_color = widget.config.get('text_color', '#212529')
                            font_size = widget.config.get('font_size', 16)
                            content.setStyleSheet(f"color: {text_color}; font-size: {font_size}px; font-weight: bold;")
                
                widget.on_message_received = on_message_received
                
            elif widget_type in ['gauge', 'gauge_circular', 'gauge_linear', 'gauge_speedometer']:
                from PyQt6.QtWidgets import QLabel
                from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygon
                from PyQt6.QtCore import QRect, QPoint
                import math
                
                # Create a custom gauge widget
                gauge_widget = QWidget()
                gauge_widget.setMinimumSize(100, 80)
                gauge_widget.value = 0
                gauge_widget.gauge_type = widget_type
                
                def paintEvent(event):
                    painter = QPainter(gauge_widget)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    
                    rect = gauge_widget.rect()
                    center = rect.center()
                    
                    # Get config values
                    min_val = widget.config.get('min_value', 0.0)
                    max_val = widget.config.get('max_value', 100.0)
                    accent_color = widget.config.get('accent_color', '#0d6efd')
                    text_color = widget.config.get('text_color', '#000000')
                    font_size = widget.config.get('font_size', 12)
                    
                    if gauge_widget.gauge_type == 'gauge_circular':
                        # Full circle gauge
                        radius = min(rect.width(), rect.height()) // 2 - 20
                        
                        # Draw background circle
                        pen = QPen(QColor(200, 200, 200), 6)
                        painter.setPen(pen)
                        painter.drawEllipse(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
                        
                        # Draw value arc
                        if max_val > min_val:
                            normalized_value = max(0, min(1, (gauge_widget.value - min_val) / (max_val - min_val)))
                            value_angle = int(normalized_value * 360 * 16)
                            
                            warning_color = widget.get_warning_color(gauge_widget.value)
                            arc_color = QColor(warning_color) if warning_color else QColor(accent_color)
                            pen.setColor(arc_color)
                            painter.setPen(pen)
                            painter.drawArc(center.x() - radius, center.y() - radius,
                                           radius * 2, radius * 2, 90 * 16, -value_angle)
                    
                    elif gauge_widget.gauge_type == 'gauge_linear':
                        # Horizontal bar gauge
                        bar_height = 20
                        bar_width = rect.width() - 40
                        bar_x = 20
                        bar_y = center.y() - bar_height // 2
                        
                        # Draw background bar
                        painter.setPen(QPen(QColor(200, 200, 200), 2))
                        painter.setBrush(QBrush(QColor(240, 240, 240)))
                        painter.drawRect(bar_x, bar_y, bar_width, bar_height)
                        
                        # Draw value bar
                        if max_val > min_val:
                            normalized_value = max(0, min(1, (gauge_widget.value - min_val) / (max_val - min_val)))
                            value_width = int(normalized_value * bar_width)
                            
                            warning_color = widget.get_warning_color(gauge_widget.value)
                            bar_color = QColor(warning_color) if warning_color else QColor(accent_color)
                            painter.setBrush(QBrush(bar_color))
                            painter.setPen(QPen(bar_color, 1))
                            painter.drawRect(bar_x, bar_y, value_width, bar_height)
                    
                    elif gauge_widget.gauge_type == 'gauge_speedometer':
                        # Speedometer with needle
                        radius = min(rect.width(), rect.height()) // 2 - 20
                        
                        # Draw background arc
                        pen = QPen(QColor(200, 200, 200), 8)
                        painter.setPen(pen)
                        painter.drawArc(center.x() - radius, center.y() - radius,
                                       radius * 2, radius * 2, 45 * 16, 90 * 16)
                        
                        # Draw scale marks
                        painter.setPen(QPen(QColor(100, 100, 100), 2))
                        for i in range(11):  # 0-10 marks
                            angle = 45 + (i * 9)  # 45° to 135°
                            angle_rad = math.radians(angle)
                            x1 = center.x() + (radius - 10) * math.cos(angle_rad)
                            y1 = center.y() + (radius - 10) * math.sin(angle_rad)
                            x2 = center.x() + radius * math.cos(angle_rad)
                            y2 = center.y() + radius * math.sin(angle_rad)
                            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                        
                        # Draw needle
                        if max_val > min_val:
                            normalized_value = max(0, min(1, (gauge_widget.value - min_val) / (max_val - min_val)))
                            needle_angle = 45 + (normalized_value * 90)
                            needle_rad = math.radians(needle_angle)
                            
                            warning_color = widget.get_warning_color(gauge_widget.value)
                            needle_color = QColor(warning_color) if warning_color else QColor(accent_color)
                            
                            # Draw needle
                            painter.setPen(QPen(needle_color, 3))
                            needle_x = center.x() + (radius - 15) * math.cos(needle_rad)
                            needle_y = center.y() + (radius - 15) * math.sin(needle_rad)
                            painter.drawLine(center.x(), center.y(), int(needle_x), int(needle_y))
                            
                            # Draw center dot
                            painter.setBrush(QBrush(needle_color))
                            painter.drawEllipse(center.x() - 4, center.y() - 4, 8, 8)
                    
                    else:  # Default arc gauge
                        radius = min(rect.width(), rect.height()) // 2 - 15
                        
                        # Draw background arc
                        pen = QPen(QColor(200, 200, 200), 8)
                        painter.setPen(pen)
                        painter.drawArc(center.x() - radius, center.y() - radius, 
                                       radius * 2, radius * 2, 30 * 16, 120 * 16)
                        
                        # Draw value arc
                        if max_val > min_val:
                            normalized_value = max(0, min(1, (gauge_widget.value - min_val) / (max_val - min_val)))
                            value_angle = int(normalized_value * 120 * 16)
                            
                            warning_color = widget.get_warning_color(gauge_widget.value)
                            arc_color = QColor(warning_color) if warning_color else QColor(accent_color)
                            
                            pen.setColor(arc_color)
                            painter.setPen(pen)
                            painter.drawArc(center.x() - radius, center.y() - radius,
                                           radius * 2, radius * 2, 30 * 16, value_angle)
                    
                    # Draw value text (common for all types)
                    painter.setPen(QColor(text_color))
                    font = painter.font()
                    font.setPointSize(font_size)
                    painter.setFont(font)
                    
                    formatted_value = widget.format_value(gauge_widget.value)
                    
                    # Position text based on gauge type
                    if gauge_widget.gauge_type == 'gauge_linear':
                        from PyQt6.QtCore import QRect, Qt
                        text_rect = QRect(0, rect.bottom() - 30, rect.width(), 20)
                    else:
                        from PyQt6.QtCore import Qt
                        text_rect = rect
                    
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, formatted_value)
                    
                    # Draw min/max labels for arc gauges
                    if gauge_widget.gauge_type in ['gauge', 'gauge_speedometer']:
                        small_font = painter.font()
                        small_font.setPointSize(max(8, font_size - 4))
                        painter.setFont(small_font)
                        
                        min_text = f"{min_val:.0f}"
                        max_text = f"{max_val:.0f}"
                        
                        painter.drawText(rect.left() + 5, rect.bottom() - 5, min_text)
                        painter.drawText(rect.right() - 25, rect.bottom() - 5, max_text)
                
                gauge_widget.paintEvent = paintEvent
                widget.content_layout.addWidget(gauge_widget)
                widget.gauge_widget = gauge_widget
                
                def on_message_received(topic_msg, message):
                    if topic_msg == topic:
                        try:
                            gauge_widget.value = float(message)
                            gauge_widget.update()
                        except ValueError:
                            pass
                widget.on_message_received = on_message_received
                
            elif widget_type == 'button':
                from PyQt6.QtWidgets import QPushButton
                button = QPushButton("Toggle")
                button.setCheckable(True)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #e9ecef;
                        border: 1px solid #ced4da;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-weight: 500;
                    }
                    QPushButton:checked {
                        background-color: #0d6efd;
                        color: white;
                    }
                """)
                
                def on_click():
                    if self.mqtt:
                        self.mqtt.publish(topic, str(int(button.isChecked())))
                button.clicked.connect(on_click)
                
                widget.content_layout.addWidget(button)
                widget.button_widget = button
                
                def on_message_received(topic_msg, message):
                    if topic_msg == topic:
                        try:
                            button.setChecked(bool(int(message)))
                        except ValueError:
                            pass
                widget.on_message_received = on_message_received
            
            elif widget_type == 'slider':
                from PyQt6.QtWidgets import QSlider, QLabel
                from PyQt6.QtCore import Qt
                
                # Create slider
                slider = QSlider(Qt.Orientation.Horizontal)
                min_val = widget.config.get('min_value', 0.0)
                max_val = widget.config.get('max_value', 100.0)
                slider.setMinimum(int(min_val))
                slider.setMaximum(int(max_val))
                slider.setValue(int(min_val))
                
                # Create value display
                value_label = QLabel(str(int(min_val)))
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Style the slider
                accent_color = widget.config.get('accent_color', '#0d6efd')
                slider.setStyleSheet(f"""
                    QSlider::groove:horizontal {{
                        border: 1px solid #ced4da;
                        height: 8px;
                        background: #e9ecef;
                        margin: 0px;
                        border-radius: 4px;
                    }}
                    QSlider::handle:horizontal {{
                        background: {accent_color};
                        border: 1px solid {accent_color};
                        width: 16px;
                        margin: -4px 0;
                        border-radius: 8px;
                    }}
                    QSlider::handle:horizontal:hover {{
                        background: {accent_color};
                        opacity: 0.8;
                    }}
                """)
                
                # Style value label
                text_color = widget.config.get('text_color', '#212529')
                font_size = widget.config.get('font_size', 14)
                value_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        font-size: {font_size}px;
                        font-weight: bold;
                        padding: 4px;
                    }}
                """)
                
                # Flag to prevent feedback loops
                widget._updating_from_mqtt = False
                
                def on_value_changed(value):
                    # Only publish if user changed it, not MQTT
                    if not widget._updating_from_mqtt:
                        try:
                            formatted_value = widget.format_value(value)
                            if hasattr(widget, 'value_label') and widget.value_label:
                                widget.value_label.setText(formatted_value)
                            if self.mqtt:
                                self.mqtt.publish(topic, str(value))
                        except (RuntimeError, AttributeError):
                            pass
                
                slider.valueChanged.connect(on_value_changed)
                
                # Add to layout
                widget.content_layout.addWidget(value_label)
                widget.content_layout.addWidget(slider)
                widget.slider_widget = slider
                widget.value_label = value_label
                
                def on_message_received(topic_msg, message):
                    if topic_msg == topic:
                        try:
                            # Check if widgets still exist and are valid
                            if (hasattr(widget, 'slider_widget') and widget.slider_widget and 
                                hasattr(widget, 'value_label') and widget.value_label and
                                not widget.slider_widget.isHidden()):
                                
                                # Set flag to prevent feedback loop
                                widget._updating_from_mqtt = True
                                
                                value = int(float(message))
                                # Clamp value to slider range
                                min_val = widget.slider_widget.minimum()
                                max_val = widget.slider_widget.maximum()
                                value = max(min_val, min(max_val, value))
                                
                                widget.slider_widget.setValue(value)
                                formatted_value = widget.format_value(value)
                                widget.value_label.setText(formatted_value)
                                
                                # Reset flag
                                widget._updating_from_mqtt = False
                                
                        except (ValueError, RuntimeError, AttributeError):
                            # Reset flag on error
                            widget._updating_from_mqtt = False
                widget.on_message_received = on_message_received
            
            # Position the widget
            if x is None or y is None:
                x, y = self.find_next_position()
            
            # Snap to grid
            x = round(x / self.grid_size) * self.grid_size
            y = round(y / self.grid_size) * self.grid_size
            
            widget.move(x, y)
            widget.resize(160, 120)  # Default size
            
            self.widgets.append(widget)
            
            # Subscribe to MQTT topic
            if self.mqtt and topic:
                if topic not in self.subscribed_topics:
                    print(f"[DEBUG] Subscribing to topic: {topic}")
                    self.mqtt.subscribe(topic)
                    self.subscribed_topics.add(topic)
                
                # Connect MQTT messages
                if hasattr(widget, 'on_message_received'):
                    self.mqtt.message_received.connect(widget.on_message_received)
                    print(f"[DEBUG] Connected message_received signal for {widget_type} widget")
            
            widget.show()
            return widget
            
        except Exception as e:
            error_msg = f"Failed to add {widget_type} widget: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            return None
    
    def find_empty_cell(self):
        """Find the next empty cell in the grid
        
        Returns:
            tuple: (row, col) of the first empty cell found
        """
        max_cols = 3  # Default number of columns
        
        # First try to find an empty cell in existing rows
        for row in range(self.grid_layout.rowCount()):
            for col in range(max_cols):
                if self.grid_layout.itemAtPosition(row, col) is None:
                    return (row, col)
        
        # If no empty cells found, add a new row
        return (self.grid_layout.rowCount(), 0)
    
    def find_next_position(self):
        """Find the next available position for absolute positioning"""
        # Simple grid-based positioning
        x, y = 20, 20  # Start position
        
        # Check existing widgets to avoid overlap
        for widget in self.widgets:
            widget_rect = widget.geometry()
            # If position would overlap, move to next grid position
            if abs(widget_rect.x() - x) < 180 and abs(widget_rect.y() - y) < 140:
                x += 180  # Move right
                if x > 800:  # Wrap to next row
                    x = 20
                    y += 140
        
        return x, y
    
    def save_layout(self, file_path=None):
        """Save the current dashboard layout to a file with widget positions and sizes
        
        Args:
            file_path: Path to save the layout to. If None, a file dialog will be shown.
            
        Returns:
            bool: True if the layout was saved successfully, False otherwise
        """
        try:
            if file_path is None:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Layout",
                    "",
                    "JSON Files (*.json);;All Files (*)",
                    options=QFileDialog.Option.DontConfirmOverwrite
                )
                if not file_path:
                    return False
            
            layout_data = {
                'widgets': []
            }
            
            # Save widget data with absolute positions
            for i, widget in enumerate(self.widgets):
                if widget is not None:
                    try:
                        geometry = widget.geometry()
                        
                        widget_data = {
                            'type': widget.widget_type,
                            'topic': widget.topic,
                            'x': geometry.x(),
                            'y': geometry.y(),
                            'width': geometry.width(),
                            'height': geometry.height(),
                            'config': widget.config,
                            'value': widget.get_value() if hasattr(widget, 'get_value') else ""
                        }
                        
                        layout_data['widgets'].append(widget_data)
                    except Exception as e:
                        print(f"Failed to save widget {i}: {str(e)}")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(layout_data, f, indent=4)
                
            # Update the current layout file
            self.current_layout_file = file_path
            
            # If we have a parent with settings, update the last layout file
            if hasattr(self.parent(), 'settings'):
                if not hasattr(self.parent(), 'settings'):
                    self.parent().settings = {}
                self.parent().settings['layout_file'] = file_path
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to load layout: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            return False
    
    def set_presentation_mode(self, enabled):
        """Toggle presentation mode for all widgets"""
        self.presentation_mode = enabled
        self.container.show_grid = not enabled
        self.container.update()  # Refresh grid display
        
        for widget in self.widgets:
            if widget is not None:
                widget.set_presentation_mode(enabled)
    
    def set_widget_opacity(self, opacity):
        """Set opacity for all widgets"""
        for widget in self.widgets:
            if widget is not None:
                widget.setWindowOpacity(opacity)
    
    def load_layout(self, file_path=None):
        """Load a dashboard layout from a file
        
        Args:
            file_path: Path to the layout file. If None, a file dialog will be shown.
            
        Returns:
            bool: True if the layout was loaded successfully, False otherwise
        """
        try:
            if file_path is None:
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Load Layout",
                    "",
                    "JSON Files (*.json);;All Files (*)",
                    options=QFileDialog.Option.DontUseNativeDialog
                )
                
                if not file_path or not os.path.exists(file_path):
                    return False  # User cancelled or file doesn't exist
            
            # Clear existing widgets
            self.clear_widgets()
            
            # Load the layout data
            with open(file_path, 'r') as f:
                layout_data = json.load(f)
            
            # Check version
            version = layout_data.get('version', 1)
            
            # Create widgets from the layout data
            for widget_data in layout_data.get('widgets', []):
                widget_type = widget_data.get('type')
                topic = widget_data.get('topic')
                x = widget_data.get('x', 20)
                y = widget_data.get('y', 20)
                width = widget_data.get('width', 160)
                height = widget_data.get('height', 120)
                config = widget_data.get('config', {})
                
                if not widget_type or not topic:
                    print(f"Skipping widget with missing type or topic: {widget_data}")
                    continue
                
                # Create the widget
                widget = self.add_widget(widget_type, topic, x=x, y=y)
                
                if widget:
                    # Restore size and configuration
                    widget.resize(width, height)
                    widget.config = config
                    widget.apply_config()

                    # Restore widget-specific state
                    if 'value' in widget_data:
                        try:
                            if hasattr(widget, 'set_value'):
                                widget.set_value(widget_data['value'])
                        except Exception as e:
                            print(f"Failed to set value for {widget_type} widget: {str(e)}")

            # Update the current layout file
            self.current_layout_file = file_path

            # If we have a parent with settings, update the last layout file
            if hasattr(self.parent(), 'settings'):
                if not hasattr(self.parent(), 'settings'):
                    self.parent().settings = {}
                self.parent().settings['layout_file'] = file_path

            return True

        except Exception as e:
            error_msg = f"Failed to load layout: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            return False
    
    def clear_widgets(self):
        """Remove all widgets from the dashboard"""
        print(f"[DEBUG] Clearing {len(self.widgets)} widgets")
        
        # Make a copy of the widgets list to avoid modification during iteration
        for widget in self.widgets[:]:
            try:
                if widget is not None:
                    print(f"[DEBUG] Removing widget: {widget.widget_type} - {widget.topic}")
                    widget.setParent(None)
                    widget.hide()
                    widget.deleteLater()
            except RuntimeError:
                # Widget already deleted
                pass

        # Clear the widgets list and subscriptions
        self.widgets.clear()
        self.subscribed_topics.clear()
        print("[DEBUG] All widgets cleared")

    def show_context_menu(self, position):
        """Show context menu for the dashboard

        Args:
            position: The position where the context menu was triggered
        """
        menu = QMenu(self)

        # Add menu items
        add_action = menu.addAction("Add Widget")
        save_action = menu.addAction("Save Layout")
        load_action = menu.addAction("Load Layout")
        clear_action = menu.addAction("Clear All Widgets")

        # Show menu and get selected action
        action = menu.exec(self.mapToGlobal(position))

        # Handle the selected action
        if action == add_action:
            self.show_add_widget_dialog()
        elif action == save_action:
            self.save_layout()
        elif action == load_action:
            # Ask for confirmation if there are existing widgets
            if self.widgets:
                reply = QMessageBox.question(
                    self,
                    'Confirm Clear',
                    'Loading a layout will remove all current widgets. Continue?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.load_layout()
            else:
                self.load_layout()
        elif action == clear_action:
            # Ask for confirmation before clearing
            reply = QMessageBox.question(
                self,
                'Confirm Clear',
                'Are you sure you want to remove all widgets?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.clear_widgets()
    
    def clear_widgets(self):
        """Remove all widgets from the dashboard"""
        # Make a copy of the widgets list to avoid modification during iteration
        for widget in self.widgets[:]:
            try:
                if widget is not None:
                    widget.setParent(None)
                    widget.hide()
                    widget.deleteLater()
            except RuntimeError:
                # Widget already deleted
                pass
        
        # Clear the widgets list and subscriptions
        self.widgets.clear()
        self.subscribed_topics.clear()
    
    def show_context_menu(self, position):
        """Show context menu for the dashboard
        
        Args:
            position: The position where the context menu was triggered
        """
        menu = QMenu(self)
        
        # Add menu items
        add_action = menu.addAction("Add Widget")
        save_action = menu.addAction("Save Layout")
        load_action = menu.addAction("Load Layout")
        clear_action = menu.addAction("Clear All Widgets")
        
        # Show menu and get selected action
        action = menu.exec(self.mapToGlobal(position))
        
        # Handle the selected action
        if action == add_action:
            self.show_add_widget_dialog()
        elif action == save_action:
            self.save_layout()
        elif action == load_action:
            # Ask for confirmation if there are existing widgets
            if self.widgets:
                reply = QMessageBox.question(
                    self,
                    'Confirm Clear',
                    'Loading a layout will remove all current widgets. Continue?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.load_layout()
            else:
                self.load_layout()
        elif action == clear_action:
            # Ask for confirmation before clearing
            reply = QMessageBox.question(
                self,
                'Confirm Clear',
                'Are you sure you want to remove all widgets?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.clear_widgets()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event for widget drag and drop"""
        if event.mimeData().hasFormat('application/x-widget'):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event for widget drag and drop"""
        if event.mimeData().hasFormat('application/x-widget'):
            # Get the widget type from the mime data
            widget_type = event.mimeData().data('application/x-widget').data().decode()
            
            # Get the drop position in grid coordinates
            pos = event.position().toPoint()
            widget_under_cursor = self.childAt(pos)
            
            # Find the drop position in the grid
            if widget_under_cursor:
                # Get the widget that was clicked on (might be a child of the actual widget)
                while widget_under_cursor.parent() and widget_under_cursor.parent() != self.container:
                    widget_under_cursor = widget_under_cursor.parent()
                
                # Get the widget's position in the grid
                index = self.grid_layout.indexOf(widget_under_cursor)
                if index >= 0:
                    row, col, _, _ = self.grid_layout.getItemPosition(index)
                else:
                    # If we couldn't find the widget in the layout, use the mouse position
                    row = pos.y() // 100  # Approximate row height
                    col = pos.x() // 150   # Approximate column width
            else:
                # If no widget was under the cursor, use the mouse position
                row = pos.y() // 100  # Approximate row height
                col = pos.x() // 150   # Approximate column width
            
            # Limit the position to reasonable values
            row = max(0, min(row, 100))  # Limit to 100 rows
            col = max(0, min(col, 10))   # Limit to 10 columns
            
            # Show dialog to get MQTT topic
            topic, ok = QInputDialog.getText(
                self, 
                f"Add {widget_type.capitalize()} Widget", 
                f"Enter MQTT topic for {widget_type}:"
            )
            
            if ok and topic.strip():
                # Add the widget at the calculated position
                self.add_widget(widget_type, topic.strip(), row=row, col=col)
                event.acceptProposedAction()

class AddWidgetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Widget")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Widget type selection
        self.widget_type = QComboBox()
        self.widget_type.addItems(['label', 'gauge', 'gauge_circular', 'gauge_linear', 'gauge_speedometer', 'button', 'slider'])
        
        # Topic input
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("Enter MQTT topic")
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add widgets to layout
        layout.addWidget(QLabel("Widget Type:"))
        layout.addWidget(self.widget_type)
        layout.addWidget(QLabel("MQTT Topic:"))
        layout.addWidget(self.topic_edit)
        layout.addWidget(button_box)
    
    def get_selected_widget(self):
        return self.widget_type.currentText()
    
    def get_topic(self):
        return self.topic_edit.text().strip()

class BaseWidget(QFrame):
    """Base class for all dashboard widgets"""
    def __init__(self, widget_type, topic, mqtt_client, parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.topic = topic
        self.mqtt = mqtt_client
        
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
        
        # Initialize the widget
        self.init_ui()
        
        # Set up event filter for hover effects
        self.setMouseTracking(True)
        self.enterEvent = self.on_enter
        self.leaveEvent = self.on_leave
        
    def on_enter(self, event):
        # Add hover effect
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #6c757d;
                border-radius: 4px;
            }
        """)
        
    def on_leave(self, event):
        # Remove hover effect
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        
    def mousePressEvent(self, event):
        # Check if the resize handle was clicked
        if self.resize_handle.underMouse():
            self.resizing = True
            self.original_geometry = self.geometry()
            self.mouse_press_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            event.ignore()
            
    def mouseMoveEvent(self, event):
        if self.resizing and self.original_geometry:
            # Calculate new size
            delta = event.globalPosition().toPoint() - self.mouse_press_pos
            new_width = max(50, self.original_geometry.width() + delta.x())
            new_height = max(50, self.original_geometry.height() + delta.y())
            self.resize(new_width, new_height)
            event.accept()
        else:
            event.ignore()
            
    def mouseReleaseEvent(self, event):
        self.resizing = False
        
        # Create content layout
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.layout.addLayout(self.content_layout)
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.setMinimumSize(100, 80)
        
        # Title bar
        self.title_bar = QWidget()
        self.title_layout = QHBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(5, 2, 5, 2)
        
        self.title_label = QLabel(self.topic)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 10px;")
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setStyleSheet("QPushButton { font-size: 10px; }")
        self.close_btn.clicked.connect(self.deleteLater)
        
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()
        self.title_layout.addWidget(self.close_btn)
        
        self.layout.addWidget(self.title_bar)
    
    def snap_to_grid(self, pos):
        """Snap position to grid"""
        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size
        return QPoint(x, y)
    
    def snap_size_to_grid(self, size):
        """Snap size to grid"""
        w = max(self.grid_size * 2, round(size.width() / self.grid_size) * self.grid_size)
        h = max(self.grid_size * 2, round(size.height() / self.grid_size) * self.grid_size)
        return QSize(w, h)
    
    def get_resize_direction(self, pos):
        """Determine resize direction based on mouse position"""
        rect = self.rect()
        margin = self.resize_margin
        
        left = pos.x() <= margin
        right = pos.x() >= rect.width() - margin
        top = pos.y() <= margin
        bottom = pos.y() >= rect.height() - margin
        
        if left and top:
            return 'nw'
        elif right and top:
            return 'ne'
        elif left and bottom:
            return 'sw'
        elif right and bottom:
            return 'se'
        elif left:
            return 'w'
        elif right:
            return 'e'
        elif top:
            return 'n'
        elif bottom:
            return 's'
        return None
    
    def update_cursor(self, direction):
        """Update cursor based on resize direction"""
        cursors = {
            'n': Qt.CursorShape.SizeVerCursor,
            's': Qt.CursorShape.SizeVerCursor,
            'e': Qt.CursorShape.SizeHorCursor,
            'w': Qt.CursorShape.SizeHorCursor,
            'ne': Qt.CursorShape.SizeBDiagCursor,
            'sw': Qt.CursorShape.SizeBDiagCursor,
            'nw': Qt.CursorShape.SizeFDiagCursor,
            'se': Qt.CursorShape.SizeFDiagCursor
        }
        if direction in cursors:
            self.setCursor(cursors[direction])
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                self.original_geometry = self.geometry()
            else:
                self.dragging = True
                self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.resizing and self.resize_direction:
            self.handle_resize(event.pos())
        elif self.dragging:
            new_pos = self.mapToParent(event.pos() - self.offset)
            snapped_pos = self.snap_to_grid(new_pos)
            self.move(snapped_pos)
        else:
            # Update cursor when hovering
            direction = self.get_resize_direction(event.pos())
            self.update_cursor(direction)
    
    def handle_resize(self, pos):
        """Handle widget resizing"""
        if not self.original_geometry:
            return
            
        orig = self.original_geometry
        new_rect = QRect(orig)
        
        if 'n' in self.resize_direction:
            new_rect.setTop(orig.top() + pos.y())
        if 's' in self.resize_direction:
            new_rect.setBottom(orig.top() + pos.y())
        if 'w' in self.resize_direction:
            new_rect.setLeft(orig.left() + pos.x())
        if 'e' in self.resize_direction:
            new_rect.setRight(orig.left() + pos.x())
        
        # Ensure minimum size
        if new_rect.width() < self.minimumWidth():
            if 'w' in self.resize_direction:
                new_rect.setLeft(new_rect.right() - self.minimumWidth())
            else:
                new_rect.setRight(new_rect.left() + self.minimumWidth())
        
        if new_rect.height() < self.minimumHeight():
            if 'n' in self.resize_direction:
                new_rect.setTop(new_rect.bottom() - self.minimumHeight())
            else:
                new_rect.setBottom(new_rect.top() + self.minimumHeight())
        
        # Snap to grid
        snapped_size = self.snap_size_to_grid(new_rect.size())
        new_rect.setSize(snapped_size)
        
        self.setGeometry(new_rect)
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.resize_direction = None
        self.original_geometry = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def leaveEvent(self, event):
        """Reset cursor when leaving widget"""
        if not self.resizing:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def get_value(self):
        """Return the current value of the widget"""
        raise NotImplementedError("Subclasses must implement get_value()")

class LabelWidget(BaseWidget):
    def __init__(self, topic, initial_value="", mqtt_client=None, parent=None):
        super().__init__("label", topic, mqtt_client, parent)
        self.value_label = QLabel(initial_value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        
        if mqtt_client:
            mqtt_client.message_received.connect(self.on_message_received)
            
    def on_message_received(self, topic, message):
        if topic == self.topic:
            self.value_label.setText(message)
            
    def get_value(self):
        return self.value_label.text()

class ButtonWidget(BaseWidget):
    def __init__(self, topic, label="Toggle", mqtt_client=None, parent=None):
        super().__init__("button", topic, mqtt_client, parent)
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
        self.content_layout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addStretch(1)
        
    def on_click(self):
        self.state = self.button.isChecked()
        if self.mqtt:
            self.mqtt.publish(self.topic, str(int(self.state)))
            
    def get_value(self):
        return str(int(self.state))

class SliderWidget(BaseWidget):
    def __init__(self, topic, min_val=0, max_val=100, initial_val=0, mqtt_client=None, parent=None):
        super().__init__("slider", topic, mqtt_client, parent)
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
        self.value_label.setText(str(value))
        if self.mqtt:
            self.mqtt.publish(self.topic, str(value))
            
    def get_value(self):
        return str(self.slider.value())
        
    def set_value(self, value):
        try:
            self.slider.setValue(int(value))
        except (ValueError, TypeError):
            pass

class GaugeWidget(BaseWidget):
    def __init__(self, topic, min_val=0, max_val=100, initial_val=0, mqtt_client=None, parent=None):
        super().__init__("gauge", topic, mqtt_client, parent)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.value = float(initial_val)
        
        # Set minimum size
        self.setMinimumSize(120, 80)
        
        # Connect to MQTT if available
        if mqtt_client:
            mqtt_client.message_received.connect(self.on_message_received)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        margin = 5
        
        # Draw background
        painter.setBrush(QColor(248, 249, 250))  # Light gray background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, width, height, 5, 5)
        
        # Calculate gauge dimensions
        gauge_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        gauge_rect.setHeight(int(gauge_rect.height() * 0.7))  # Make room for value display
        
        # Draw background arc
        pen = QPen()
        pen.setWidth(8)
        pen.setColor(QColor(233, 236, 239))  # Light gray
        painter.setPen(pen)
        
        # Draw the background arc (semi-circle)
        start_angle = 30 * 16  # Start at 30 degrees (0 is at 3 o'clock)
        span_angle = 120 * 16  # 120 degrees span
        painter.drawArc(gauge_rect, start_angle, span_angle)
        
        # Calculate the value position
        value_range = self.max_val - self.min_val
        normalized_value = max(0, min(1, (self.value - self.min_val) / value_range))
        value_angle = int(start_angle - normalized_value * span_angle)
        
        # Draw the value arc
        pen.setColor(QColor(13, 110, 253))  # Primary blue
        painter.setPen(pen)
        painter.drawArc(gauge_rect, start_angle, value_angle - start_angle)
        
        # Draw the value text
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(33, 37, 41))  # Dark gray
        
        value_rect = QRect(gauge_rect)
        value_rect.setTop(int(gauge_rect.bottom() - 10))
        value_rect.setHeight(height - gauge_rect.bottom() - 5)
        
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:.1f}")
        
        # Draw min/max labels
        small_font = painter.font()
        small_font.setPointSize(8)
        small_font.setBold(False)
        painter.setFont(small_font)
        
        # Min label
        min_rect = QRect(gauge_rect.left() + 5, gauge_rect.bottom() - 15, 30, 15)
        painter.drawText(min_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, f"{self.min_val}")
        
        # Max label
        max_rect = QRect(gauge_rect.right() - 35, gauge_rect.bottom() - 15, 30, 15)
        painter.drawText(max_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, f"{self.max_val}")
        
    def on_message_received(self, topic, message):
        if topic == self.topic:
            try:
                self.set_value(float(message))
            except (ValueError, TypeError):
                pass
    
    def set_value(self, value):
        try:
            self.value = float(value)
            self.update()  # Trigger repaint
        except (ValueError, TypeError):
            pass
            
    def get_value(self):
        return str(self.value)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()  # Redraw gauge when resized
