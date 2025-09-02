from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QAction

class ResizableWidget(QFrame):
    def __init__(self, widget_type, topic, mqtt_client=None, parent=None, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.widget_type = widget_type
        self.topic = topic
        self.mqtt_client = mqtt_client
        self.presentation_mode = False
        
        # Grid and resize settings
        self.grid_size = 20
        self.resize_margin = 8
        
        # State variables
        self.dragging = False
        self.resizing = False
        self.resize_direction = None
        self.offset = QPoint()
        self.original_geometry = None
        
        # Setup widget
        self.setMinimumSize(100, 80)
        
        # Enable mouse tracking for resize cursors
        self.setMouseTracking(True)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Setup UI
        self.init_ui()
        
        # Apply configuration
        self.apply_config()
    
    def init_ui(self):
        """Initialize the widget UI"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        # Title bar
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(f"{self.widget_type}: {self.topic}")
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.deleteLater)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_btn)
        
        self.layout.addLayout(title_layout)
        
        # Content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.layout.addLayout(self.content_layout)
    
    def snap_to_grid(self, pos):
        """Snap position to grid"""
        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size
        return QPoint(x, y)
    
    def snap_size_to_grid(self, size):
        """Snap size to grid"""
        w = max(self.grid_size * 3, round(size.width() / self.grid_size) * self.grid_size)
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
    
    def get_resize_cursor(self, direction):
        """Get cursor for resize direction"""
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
        return cursors.get(direction, Qt.CursorShape.ArrowCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.presentation_mode:
            self.offset = event.position().toPoint()
            
            # Check if we're near an edge for resizing
            resize_dir = self.get_resize_direction(event.position().toPoint())
            if resize_dir:
                self.resizing = True
                self.resize_direction = resize_dir
                self.setCursor(self.get_resize_cursor(resize_dir))
            else:
                self.dragging = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            self.dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        if self.resizing and self.resize_direction:
            self.handle_resize(event.pos())
        elif self.dragging:
            new_pos = self.mapToParent(event.pos() - self.offset)
            snapped_pos = self.snap_to_grid(new_pos)
            self.move(snapped_pos)
        else:
            # Update cursor when hovering (only if not in presentation mode)
            if not self.presentation_mode:
                resize_dir = self.get_resize_direction(event.position().toPoint())
                if resize_dir:
                    self.setCursor(self.get_resize_cursor(resize_dir))
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
    
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
    
    def paintEvent(self, event):
        """Custom paint event to show resize handles"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw resize handles in corners
        handle_size = 6
        rect = self.rect()
        
        # Handle color
        handle_color = QColor(0, 123, 255, 150)  # Semi-transparent blue
        painter.setBrush(handle_color)
        painter.setPen(QPen(QColor(0, 123, 255), 1))
        
        # Draw corner handles
        positions = [
            (rect.left(), rect.top()),           # Top-left
            (rect.right() - handle_size, rect.top()),  # Top-right
            (rect.left(), rect.bottom() - handle_size),  # Bottom-left
            (rect.right() - handle_size, rect.bottom() - handle_size)  # Bottom-right
        ]
        
        for x, y in positions:
            painter.drawRect(x, y, handle_size, handle_size)
    
    def show_context_menu(self, position):
        """Show context menu for widget customization"""
        menu = QMenu(self)
        
        customize_action = QAction("Tilpass widget...", self)
        customize_action.triggered.connect(self.customize_widget)
        menu.addAction(customize_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Slett widget", self)
        delete_action.triggered.connect(self.deleteLater)
        menu.addAction(delete_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def customize_widget(self):
        """Open customization dialog"""
        from .widget_customization import WidgetCustomizationDialog
        
        dialog = WidgetCustomizationDialog(self.widget_type, self.config, self)
        if dialog.exec():
            self.config = dialog.get_config()
            self.apply_config()
    
    def apply_config(self):
        """Apply configuration to widget appearance"""
        # Update title
        display_name = self.config.get('display_name', self.widget_type.title())
        self.title_label.setText(display_name)
        
        # Apply colors and styling
        bg_color = self.config.get('bg_color', '#ffffff')
        text_color = self.config.get('text_color', '#212529')
        border_color = self.config.get('border_color', '#dee2e6')
        font_size = self.config.get('font_size', 16)
        border_width = self.config.get('border_width', 1)
        border_radius = self.config.get('border_radius', 4)
        
        self.setStyleSheet(f"""
            ResizableWidget {{
                background-color: {bg_color};
                border: {border_width}px solid {border_color};
                border-radius: {border_radius}px;
                color: {text_color};
                font-size: {font_size}px;
            }}
        """)
        
        # Update title label styling
        self.title_label.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                color: {text_color};
                font-size: {max(10, font_size - 2)}px;
                font-weight: bold;
                padding: 2px 4px;
                border: none;
            }}
        """)
        
        # Update close button styling
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {text_color};
                font-size: {max(12, font_size)}px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 0, 0, 0.1);
                border-radius: 2px;
            }}
        """)
        
        # Hide/show elements based on config
        if not self.config.get('show_title', True):
            self.title_label.hide()
        else:
            self.title_label.show()
            
        if not self.config.get('show_close', True):
            self.close_btn.hide()
        else:
            self.close_btn.show()
        
        # Force update gauge widget if it exists
        if hasattr(self, 'gauge_widget') and self.gauge_widget:
            self.gauge_widget.update()
        
        # Update slider widget styling if it exists
        if hasattr(self, 'slider_widget') and self.slider_widget:
            accent_color = self.config.get('accent_color', '#0d6efd')
            self.slider_widget.setStyleSheet(f"""
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
            
            # Update min/max values
            min_val = self.config.get('min_value', 0.0)
            max_val = self.config.get('max_value', 100.0)
            current_val = self.slider_widget.value()
            
            self.slider_widget.setMinimum(int(min_val))
            self.slider_widget.setMaximum(int(max_val))
            
            # Clamp current value to new range
            clamped_val = max(int(min_val), min(int(max_val), current_val))
            self.slider_widget.setValue(clamped_val)
            
            # Update value label styling and text
            if hasattr(self, 'value_label') and self.value_label:
                text_color = self.config.get('text_color', '#212529')
                font_size = self.config.get('font_size', 14)
                self.value_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        font-size: {font_size}px;
                        font-weight: bold;
                        padding: 4px;
                    }}
                """)
                formatted_value = self.format_value(clamped_val)
                self.value_label.setText(formatted_value)
    
    def set_presentation_mode(self, enabled):
        """Toggle presentation mode - hide/show frames and buttons"""
        self.presentation_mode = enabled
        
        if enabled:
            # Hide frame, title, and close button
            self.setFrameStyle(QFrame.Shape.NoFrame)
            self.title_label.hide()
            self.close_btn.hide()
            
            # Make background transparent
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0);
                    border: none;
                }
            """)
            
            # Disable resize and drag in presentation mode
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            
        else:
            # Restore normal appearance
            self.apply_config()  # This will restore proper styling
            self.title_label.show()
            self.close_btn.show()
            
            # Re-enable interactions
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
    
    def format_value(self, value):
        """Format value according to configuration"""
        try:
            # Apply conversion
            factor = self.config.get('conversion_factor', 1.0)
            offset = self.config.get('conversion_offset', 0.0)
            converted_value = float(value) * factor + offset
            
            # Format with decimal places
            decimal_places = self.config.get('decimal_places', 1)
            formatted = f"{converted_value:.{decimal_places}f}"
            
            # Add unit if specified
            unit = self.config.get('unit', '')
            if unit:
                formatted += f" {unit}"
            
            return formatted
        except (ValueError, TypeError):
            return str(value)
    
    def get_warning_color(self, value):
        """Get warning color based on value and thresholds"""
        if not self.config.get('warning_enabled', False):
            return None
        
        try:
            val = float(value)
            warning_low = self.config.get('warning_low', 20.0)
            warning_high = self.config.get('warning_high', 80.0)
            
            if val <= warning_low or val >= warning_high:
                return self.config.get('critical_color', '#dc3545')
            elif val <= warning_low * 1.2 or val >= warning_high * 0.8:
                return self.config.get('warning_color', '#ffc107')
        except (ValueError, TypeError):
            pass
        
        return None
    
    def get_value(self):
        """Return the current value of the widget"""
        return ""
