from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QDialog, QGraphicsDropShadowEffect, QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QAction, QPixmap, QIcon
from pathlib import Path

class ResizableWidget(QFrame):
    def __init__(self, widget_type, topic, mqtt_client=None, parent=None, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.widget_type = widget_type
        self.topic = topic
        self.mqtt_client = mqtt_client
        self.presentation_mode = False
        
        self.error_state = False
        self.error_message = ""
        
        self.grid_size = 20
        self.resize_margin = 8
        
        self.dragging = False
        self.resizing = False
        self.resize_direction = None
        self.offset = QPoint()
        self.original_geometry = None
        
        # --- Core Refactoring for Styling ---
        # Main frame is a transparent container for resizing and context menu
        self.setMinimumSize(100, 80)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

        # Inner container handles all appearance (background, border)
        self.background_container = QWidget(self)
        self.background_container.setObjectName("widget_background")
        
        # Add Drop Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.background_container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.background_container)

        # Setup UI inside the background container
        self.init_ui()

        # NOTE: apply_config() is NOT called here - subclasses must call it after init_content()
        
    def init_ui(self):
        """Initialize UI elements inside the background_container."""
        self.layout = QVBoxLayout(self.background_container) # Use self.layout for base ResizableWidget layout
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)

        # Title bar
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.icon_label.hide()

        display_name = self.config.get('display_name', '')
        self.title_label = QLabel(display_name or self.topic)

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.safe_delete)

        title_layout.addWidget(self.icon_label, 0)
        title_layout.addWidget(self.title_label, 0)
        title_layout.addStretch(1)
        title_layout.addWidget(self.close_btn, 0)

        self.layout.addLayout(title_layout)

        # Content area (this is where actual widget content goes)
        self.content_layout = QVBoxLayout() # Renamed from self.content_layout to self._content_layout to avoid confusion
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.layout.addLayout(self.content_layout)

        # Error state label (initially hidden)
        self.error_label = QLabel("⚠️\nInvalid Data")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.layout.addWidget(self.error_label)
        self.error_label.hide()
    
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
        
        if left and top: return 'nw'
        elif right and top: return 'ne'
        elif left and bottom: return 'sw'
        elif right and bottom: return 'se'
        elif left: return 'w'
        elif right: return 'e'
        elif top: return 'n'
        elif bottom: return 's'
        return None
    
    def get_resize_cursor(self, direction):
        """Get cursor for resize direction"""
        cursors = {
            'n': Qt.CursorShape.SizeVerCursor, 's': Qt.CursorShape.SizeVerCursor,
            'e': Qt.CursorShape.SizeHorCursor, 'w': Qt.CursorShape.SizeHorCursor,
            'ne': Qt.CursorShape.SizeBDiagCursor, 'sw': Qt.CursorShape.SizeBDiagCursor,
            'nw': Qt.CursorShape.SizeFDiagCursor, 'se': Qt.CursorShape.SizeFDiagCursor
        }
        return cursors.get(direction, Qt.CursorShape.ArrowCursor)
    
    def mousePressEvent(self, event):
        if self.presentation_mode: return
            
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.position().toPoint()
            pos = event.position().toPoint()
            self.resize_direction = self.get_resize_direction(pos)
            
            if self.resize_direction:
                self.resizing = True
                self.original_geometry = self.geometry()
            else:
                self.dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        if self.presentation_mode: return
            
        if self.resizing and self.resize_direction:
            self.handle_resize(event.pos())
        elif self.dragging:
            new_pos = self.mapToParent(event.pos() - self.offset)
            snapped_pos = self.snap_to_grid(new_pos)
            self.move(snapped_pos)
        else:
            if not self.presentation_mode:
                resize_dir = self.get_resize_direction(event.position().toPoint())
                if resize_dir: self.setCursor(self.get_resize_cursor(resize_dir))
                else: self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def handle_resize(self, pos):
        if not self.original_geometry: return
        orig, new_rect = self.original_geometry, QRect(self.original_geometry)

        if 'n' in self.resize_direction: new_rect.setTop(orig.top() + pos.y())
        if 's' in self.resize_direction: new_rect.setBottom(orig.top() + pos.y())
        if 'w' in self.resize_direction: new_rect.setLeft(orig.left() + pos.x())
        if 'e' in self.resize_direction: new_rect.setRight(orig.left() + pos.x())

        if new_rect.width() < self.minimumWidth():
            if 'w' in self.resize_direction: new_rect.setLeft(new_rect.right() - self.minimumWidth())
            else: new_rect.setRight(new_rect.left() + self.minimumWidth())

        if new_rect.height() < self.minimumHeight():
            if 'n' in self.resize_direction: new_rect.setTop(new_rect.bottom() - self.minimumHeight())
            else: new_rect.setBottom(new_rect.top() + self.minimumHeight())

        # Snap size to grid and update geometry
        snapped_size = self.snap_size_to_grid(new_rect.size())
        snapped_pos = self.snap_to_grid(new_rect.topLeft())
        self.setGeometry(QRect(snapped_pos, snapped_size))
    
    def mouseReleaseEvent(self, event):
        if self.presentation_mode: return
        self.dragging, self.resizing, self.resize_direction, self.original_geometry = False, False, None, None
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def leaveEvent(self, event):
        if not self.resizing and not self.presentation_mode: self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.presentation_mode: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        handle_size, rect = 6, self.rect()
        border_color = self.config.get('border_color', '#666666')
        handle_color = QColor(border_color)
        handle_color.setAlpha(100)
        painter.setBrush(handle_color)
        painter.setPen(QPen(QColor(border_color), 1))
        
        positions = [
            (rect.left(), rect.top()), (rect.right() - handle_size, rect.top()),
            (rect.left(), rect.bottom() - handle_size), (rect.right() - handle_size, rect.bottom() - handle_size)
        ]
        for x, y in positions: painter.drawRect(x, y, handle_size, handle_size)
    
    def show_context_menu(self, position):
        if self.presentation_mode: return

        menu = QMenu(self)
        customize_action = QAction("Customize Widget...", self)
        customize_action.triggered.connect(self.customize_widget)
        menu.addAction(customize_action)
        menu.addSeparator()
        delete_action = QAction("Delete Widget", self)
        delete_action.triggered.connect(self.safe_delete)
        menu.addAction(delete_action)
        menu.exec(self.mapToGlobal(position))

    def customize_widget(self):
        from .widget_customization import WidgetCustomizationDialog
        dialog = WidgetCustomizationDialog(self.widget_type, self.config, self)
        dialog.config_changed.connect(self.apply_config) # Live preview
        if dialog.exec():
            self.config = dialog.get_config()
            self.apply_config()
    
    def safe_delete(self):
        parent_dashboard = self.parent()
        while parent_dashboard:
            if hasattr(parent_dashboard, 'remove_widget'):
                parent_dashboard.remove_widget(self)
                break
            parent_dashboard = parent_dashboard.parent()
        
        if self.mqtt_client and hasattr(self, 'on_message_received'):
            try: self.mqtt_client.message_received.disconnect(self.on_message_received)
            except (RuntimeError, TypeError): pass
            except Exception as e: print(f"[WARNING] Error disconnecting MQTT signal: {e}")
            
        self.deleteLater()

    def set_presentation_mode(self, enabled):
        self.presentation_mode = enabled

        if enabled:
            # Hide title and close button, but keep widget background and content visible
            self.title_label.hide()
            self.close_btn.hide()
            self.icon_label.hide()

            # Remove border but keep background for visibility
            # Support both 'bg_color' (from widget customization) and 'background_color' (from themes)
            bg_color = self.config.get('bg_color', self.config.get('background_color', '#1e1e1e'))
            border_radius = self.config.get('border_radius', 6)

            # Support both 'opacity' (0-100) and 'individual_opacity' (0.0-1.0)
            opacity = self.config.get('opacity', 100)
            individual_opacity = self.config.get('individual_opacity')
            if individual_opacity is not None:
                # individual_opacity is 0.0-1.0, convert to 0-100
                opacity = int(individual_opacity * 100)

            # Convert opacity (0-100) to alpha (0-255)
            alpha = int(opacity * 2.55)
            bg_with_alpha = QColor(bg_color)
            bg_with_alpha.setAlpha(alpha)

            self.background_container.setStyleSheet(f"""
                #widget_background {{
                    background-color: {bg_with_alpha.name(QColor.NameFormat.HexArgb)};
                    border: none;
                    border-radius: {border_radius}px;
                }}
            """)

            # Disable mouse interaction for moving/resizing
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowTransparentForInput)
        else:
            # Restore normal appearance
            self.apply_config()
            self.title_label.show()
            self.close_btn.show()
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowTransparentForInput)

        # Ensure correct flags for resizing/dragging in and out of presentation mode
        self.setMouseTracking(not enabled) # Disable mouse tracking for cursor changes
        self.setCursor(Qt.CursorShape.ArrowCursor) # Reset cursor

    def apply_config(self):
        """Apply configuration styling to the widget."""
        # Update title
        display_name = self.config.get('display_name', '')
        self.title_label.setText(display_name or self.topic)

        # Update header icon
        self._update_header_icon()

        # Apply background styling
        # Support both 'bg_color' (from widget customization) and 'background_color' (from themes)
        bg_color = self.config.get('bg_color', self.config.get('background_color', '#1e1e1e'))
        border_color = self.config.get('border_color', '#666666')
        border_width = self.config.get('border_width', 2)
        border_radius = self.config.get('border_radius', 6)

        # Support both 'opacity' (0-100) and 'individual_opacity' (0.0-1.0)
        opacity = self.config.get('opacity', 100)
        individual_opacity = self.config.get('individual_opacity')
        if individual_opacity is not None:
            # individual_opacity is 0.0-1.0, convert to 0-100
            opacity = int(individual_opacity * 100)

        # Convert opacity (0-100) to alpha (0-255)
        alpha = int(opacity * 2.55)
        bg_with_alpha = QColor(bg_color)
        bg_with_alpha.setAlpha(alpha)

        self.background_container.setStyleSheet(f"""
            #widget_background {{
                background-color: {bg_with_alpha.name(QColor.NameFormat.HexArgb)};
                border: {border_width}px solid {border_color};
                border-radius: {border_radius}px;
            }}
        """)

    def _update_header_icon(self):
        """Update the header icon based on config."""
        icon_data = self.config.get('icon_data', '')
        is_text = self.config.get('icon_is_text', False)
        icon_size = self.config.get('icon_size', 24)

        if not icon_data:
            self.icon_label.hide()
            return

        if is_text:
            # Text icon (emoji or unicode character)
            self.icon_label.setText(icon_data)
            self.icon_label.setStyleSheet(f"font-size: {icon_size}px;")
            self.icon_label.setFixedSize(icon_size + 4, icon_size + 4)
        else:
            # File path icon
            icon_path = Path(icon_data)
            if icon_path.exists():
                pixmap = QPixmap(str(icon_path))
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.icon_label.setPixmap(scaled_pixmap)
                    self.icon_label.setFixedSize(icon_size, icon_size)
                else:
                    self.icon_label.hide()
                    return
            else:
                self.icon_label.hide()
                return

        self.icon_label.show()

    def format_value(self, value):
        if self.error_state: self.clear_error()
        try:
            factor, offset = float(self.config.get('conversion_factor', 1.0)), float(self.config.get('conversion_offset', 0.0))
            converted_value = float(value) * factor + offset
            decimal_places = int(self.config.get('decimal_places', 1))
            formatted = f"{converted_value:.{decimal_places}f}"
            unit = self.config.get('unit', '')
            if unit: formatted += f" {unit}"
            return formatted
        except (ValueError, TypeError):
            unit = self.config.get('unit', '')
            if unit: return f"{value} {unit}"
            return str(value)
    
    def get_warning_color(self, value):
        if not self.config.get('warning_enabled', False): return None
        try:
            val, low, high = float(value), self.config.get('warning_low', 20.0), self.config.get('warning_high', 80.0)
            if val <= low or val >= high: return self.config.get('critical_color', '#dc3545')
            elif val <= low * 1.2 or val >= high * 0.8: return self.config.get('warning_color', '#ffc107')
        except (ValueError, TypeError): pass
        return None
    
    def show_error(self, message):
        self.error_state, self.error_message = True, message
        self.setToolTip(f"Error: {message}")
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if widget: widget.hide()
        self.error_label.show()
        border_width, border_radius, error_border_color = self.config.get('border_width', 2), self.config.get('border_radius', 6), "#dc3545"
        self.background_container.setStyleSheet(self.background_container.styleSheet() + f"border: {border_width}px solid {error_border_color};")

    def clear_error(self):
        if not self.error_state: return
        self.error_state, self.error_message = False, ""
        self.setToolTip("")
        self.error_label.hide()
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if widget: widget.show()
        self.apply_config()

    def get_value(self): return ""
