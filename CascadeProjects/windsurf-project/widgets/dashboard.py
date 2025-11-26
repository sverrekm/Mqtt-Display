from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QMessageBox, QFileDialog, QMenu, QInputDialog, QDialog, QComboBox, QLineEdit, QDialogButtonBox, QLabel
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QFont
import json
import os
from .grid_container import GridContainer

class Dashboard(QWidget):
    def __init__(self, mqtt_client, parent=None):
        super().__init__(parent)
        self.main_window = self.get_main_window()
        self.mqtt_client = mqtt_client
        self.widgets = []
        self.current_layout_file = None
        self.grid_size = 20
        self.presentation_mode = False
        
        self.container = GridContainer(self.grid_size)
        self.container.setMinimumSize(500, 300)
        
        # Add the welcome message label
        self.welcome_label = QLabel(
            "Welcome to MQTT Dashboard!\n\n"
            "Right-click to add a widget or load a layout to get started.",
            self.container
        )
        font = QFont()
        font.setPointSize(16)
        self.welcome_label.setFont(font)
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("color: #888;")
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        self._update_welcome_message_visibility()

    def get_main_window(self):
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QWidget) and parent.isWindow():
                return parent
            parent = parent.parent()
        return None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Center the welcome label within the container
        self.welcome_label.setGeometry(0, 0, self.container.width(), self.container.height())

    def _update_welcome_message_visibility(self):
        """Show or hide the welcome message based on widget presence."""
        if not self.widgets:
            self.welcome_label.show()
        else:
            self.welcome_label.hide()

    def set_widget_opacity(self, opacity):
        """Set opacity for all widgets."""
        for widget in self.widgets:
            if widget:
                widget.config['individual_opacity'] = opacity
                widget.apply_config()

    def set_presentation_mode(self, enabled):
        """Toggle presentation mode - hide/show frames and enable transparency"""
        self.presentation_mode = enabled
        if enabled:
            # Hide welcome message in presentation mode
            self.welcome_label.hide()

            # Disable auto-fill on all levels
            self.setAutoFillBackground(False)
            self.scroll.setAutoFillBackground(False)
            self.scroll.viewport().setAutoFillBackground(False)
            self.container.setAutoFillBackground(False)

            # Set transparent stylesheets - everything invisible except widgets
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    background: transparent;
                }
            """)
            self.scroll.setStyleSheet("""
                QScrollArea {
                    background-color: transparent;
                    background: transparent;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: transparent;
                }
            """)
            self.container.setStyleSheet("""
                #grid_container {
                    background-color: transparent;
                    background: transparent;
                }
            """)

            # Hide grid in presentation mode
            self.container.show_grid = False
            self.container.update()

            # Disable context menu in presentation mode (will be handled separately)
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

            # Set presentation mode on all widgets
            for widget in self.widgets:
                if widget and hasattr(widget, 'set_presentation_mode'):
                    widget.set_presentation_mode(True)

        else:
            # Show welcome message if needed
            self._update_welcome_message_visibility()

            # Restore normal appearance
            self.setAutoFillBackground(True)
            self.scroll.setAutoFillBackground(True)
            self.scroll.viewport().setAutoFillBackground(True)
            self.container.setAutoFillBackground(True)

            # Clear transparent stylesheets
            self.setStyleSheet("")
            self.scroll.setStyleSheet("")
            self.container.setStyleSheet("")

            # Show grid again
            self.container.show_grid = True
            self.container.update()

            # Re-enable context menu
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

            # Restore normal mode on all widgets
            for widget in self.widgets:
                if widget and hasattr(widget, 'set_presentation_mode'):
                    widget.set_presentation_mode(False)

    def add_widget(self, widget_type, topic, x=None, y=None, width=None, height=None, config=None):
        """Dynamically add a widget to the dashboard."""
        try:
            WidgetClass = None
            if widget_type == 'label':
                from .label_widget import LabelWidget
                WidgetClass = LabelWidget
            elif widget_type in ['gauge', 'gauge_circular', 'gauge_linear', 'gauge_speedometer', 'gauge_voltage']:
                from .gauge_widget import GaugeWidget
                WidgetClass = GaugeWidget
                # Ensure the specific gauge type is in the config
                if config:
                    config['type'] = widget_type
                else:
                    config = {'type': widget_type}
            elif widget_type == 'slider':
                from .slider_widget import SliderWidget
                WidgetClass = SliderWidget
            elif widget_type == 'toggle':
                from .toggle_widget import ToggleWidget
                WidgetClass = ToggleWidget
            elif widget_type == 'button':
                from .button_widget import ButtonWidget
                WidgetClass = ButtonWidget

            if not WidgetClass:
                raise ValueError(f"Unknown widget type: {widget_type}")

            # Default position if not specified
            if x is None or y is None:
                x, y = self._find_next_position()

            # Default size if not specified - ensure int values
            width = int(width) if width is not None else 200
            height = int(height) if height is not None else 160
            x = int(x)
            y = int(y)

            widget = WidgetClass(topic, self.mqtt_client, self.container, config)
            widget.setGeometry(x, y, width, height)
            widget.show()
            self.widgets.append(widget)
            self._update_welcome_message_visibility() # Update visibility
            return widget
        except Exception as e:
            print(f"[ERROR] Failed to add widget: {e}")
            import traceback
            traceback.print_exc()
            return None

    def remove_widget(self, widget):
        """Remove a widget from the dashboard."""
        if widget in self.widgets:
            self.widgets.remove(widget)
            self._update_welcome_message_visibility()

    def _find_next_position(self):
        # Simple logic to find an empty spot. Can be improved.
        x, y = 20, 20
        occupied_rects = [w.geometry() for w in self.widgets]
        while any(rect.intersects(QRect(x, y, 100, 100)) for rect in occupied_rects):
            x += self.grid_size * 2
            if x > self.container.width() - 100:
                x = 20
                y += self.grid_size * 2
        return x, y

    def save_layout(self):
        """Save the current layout to a JSON file."""
        if not self.current_layout_file:
            # Suggest a filename if no layout is loaded
            suggested_path = os.path.join(os.getcwd(), "my_layout.json")
        else:
            suggested_path = self.current_layout_file

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Layout", suggested_path, "JSON Files (*.json)")
        if not file_path:
            return

        layout_data = []
        for widget in self.widgets:
            if widget:
                widget_data = {
                    'type': widget.config.get('type', widget.widget_type), # Use specific type from config if available (for gauges)
                    'topic': widget.topic,
                    'x': widget.x(),
                    'y': widget.y(),
                    'width': widget.width(),
                    'height': widget.height(),
                    'config': widget.config
                }
                layout_data.append(widget_data)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=4)
            self.current_layout_file = file_path
            if self.main_window and hasattr(self.main_window, 'statusBar'):
                self.main_window.statusBar().showMessage(f"Layout saved to {os.path.basename(file_path)}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save layout: {e}")

    def load_layout(self, file_path=None):
        """Load a layout from a JSON file."""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Load Layout", "", "JSON Files (*.json)")
        
        if not file_path or not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                layout_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load or parse layout file: {e}")
            return
            
        self.clear_widgets()

        widget_list = []
        if isinstance(layout_data, dict) and 'widgets' in layout_data:
            widget_list = layout_data.get('widgets', [])
        elif isinstance(layout_data, list):
            widget_list = layout_data

        for widget_data in widget_list:
            if not isinstance(widget_data, dict):
                print(f"Skipping invalid widget data (not a dict): {widget_data}")
                continue

            self.add_widget(
                widget_type=widget_data.get('type'),
                topic=widget_data.get('topic'),
                x=widget_data.get('x'),
                y=widget_data.get('y'),
                width=widget_data.get('width'),
                height=widget_data.get('height'),
                config=widget_data.get('config')
            )
        
        self.current_layout_file = file_path
        if self.main_window and hasattr(self.main_window, 'statusBar'):
            self.main_window.statusBar().showMessage(f"Layout '{os.path.basename(file_path)}' loaded", 5000)
        
        self._update_welcome_message_visibility()

    def clear_widgets(self):
        """Remove all widgets from the dashboard."""
        for widget in self.widgets[:]:
            widget.setParent(None)
            widget.deleteLater()
        self.widgets.clear()
        self._update_welcome_message_visibility() # Update visibility

    def show_context_menu(self, position):
        """Show context menu for the dashboard."""
        menu = QMenu(self)

        # If in presentation mode, only show exit option
        if self.presentation_mode:
            exit_presentation_action = menu.addAction("Avslutt Presentasjonsmodus")
            action = menu.exec(self.mapToGlobal(position))

            if action == exit_presentation_action:
                # Call the main window's toggle_presentation_mode
                if self.main_window and hasattr(self.main_window, 'toggle_presentation_mode'):
                    self.main_window.toggle_presentation_mode()
            return

        # Normal menu when not in presentation mode
        add_action = menu.addAction("Add Widget...")
        menu.addSeparator()
        save_action = menu.addAction("Save Layout As...")
        load_action = menu.addAction("Load Layout...")
        menu.addSeparator()
        clear_action = menu.addAction("Clear All Widgets")

        # Disable save if there's nothing to save
        save_action.setEnabled(bool(self.widgets))
        clear_action.setEnabled(bool(self.widgets))

        action = menu.exec(self.mapToGlobal(position))

        if action == add_action:
            self.show_add_widget_dialog()
        elif action == save_action:
            self.save_layout()
        elif action == load_action:
            self.load_layout()
        elif action == clear_action:
            reply = QMessageBox.question(self, 'Confirm Clear', 'Are you sure you want to remove all widgets?',
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                           QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.clear_widgets()

    def show_add_widget_dialog(self):
        """Show dialog to add a new widget."""
        dialog = AddWidgetDialog(self)
        if dialog.exec():
            widget_type = dialog.widget_type.currentText()
            topic = dialog.topic_edit.text()
            if widget_type and topic:
                self.add_widget(widget_type, topic)

class AddWidgetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Widget")
        self.setStyleSheet("""
            QDialog {
                background-color: #2B2B2B;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
            }
            QLineEdit, QComboBox {
                background-color: #4A4A4A;
                color: #E0E0E0;
                border: 1px solid #5A5A5A;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005C99;
            }
        """)
        layout = QVBoxLayout(self)
        
        self.widget_type = QComboBox()
        self.widget_type.addItems([
            'label', 'gauge', 'gauge_circular', 'gauge_linear', 'button', 'slider', 'toggle'
        ])
        layout.addWidget(QLabel("Widget Type:"))
        layout.addWidget(self.widget_type)

        self.topic_edit = QLineEdit()
        layout.addWidget(QLabel("MQTT Topic:"))
        layout.addWidget(self.topic_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)