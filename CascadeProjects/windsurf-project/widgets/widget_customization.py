from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QCheckBox, QComboBox,
                             QPushButton, QColorDialog, QDoubleSpinBox, QFormLayout,
                             QSpinBox, QGroupBox, QScrollArea, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
from .icon_picker import IconPickerDialog
from config.themes import get_theme_list, get_theme_config
from pathlib import Path

class WidgetCustomizationDialog(QDialog):
    config_changed = pyqtSignal(dict)

    def __init__(self, widget_type, current_config=None, parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.config = current_config or {}
        self.setWindowTitle("Widget Settings")
        self.setMinimumSize(600, 700)  # Increased size for icon settings
        self.init_ui()
        self.load_config()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.general_tab = QWidget()
        self.appearance_tab = QWidget()
        self.data_tab = QWidget()

        self.init_general_tab()
        self.init_appearance_tab()
        self.init_data_tab()

        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.appearance_tab, "Appearance")
        if self.widget_type in ['gauge', 'label', 'slider', 'toggle', 'button']:
             self.tabs.addTab(self.data_tab, "Data & Units")

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

    def init_general_tab(self):
        layout = QFormLayout(self.general_tab)
        self.display_name_edit = QLineEdit()
        layout.addRow("Display Name:", self.display_name_edit)
        self.show_title = QCheckBox("Show Title")
        layout.addRow(self.show_title)
        self.show_text = QCheckBox("Show Text/Value")
        self.show_text.setChecked(True)
        layout.addRow(self.show_text)
        self.display_name_edit.textChanged.connect(self._emit_config_changed)
        self.show_title.stateChanged.connect(self._emit_config_changed)
        self.show_text.stateChanged.connect(self._emit_config_changed)
        
    def init_appearance_tab(self):
        layout = QFormLayout(self.appearance_tab)
        
        self.theme_selector = QComboBox()
        self.theme_selector.addItem("Use Global Theme", "use_global")
        self.theme_selector.addItem("Custom", "custom")
        for theme_key, theme_name, _ in get_theme_list():
            self.theme_selector.addItem(theme_name, theme_key)
        self.theme_selector.currentIndexChanged.connect(self._emit_config_changed)
        layout.addRow("Theme:", self.theme_selector)

        self.bg_color_btn = QPushButton()
        self.text_color_btn = QPushButton()
        self.border_color_btn = QPushButton()
        layout.addRow("Background Color:", self.bg_color_btn)
        layout.addRow("Text Color:", self.text_color_btn)
        layout.addRow("Border Color:", self.border_color_btn)
        self.bg_color_btn.clicked.connect(lambda: self._choose_color('bg_color'))
        self.text_color_btn.clicked.connect(lambda: self._choose_color('text_color'))
        self.border_color_btn.clicked.connect(lambda: self._choose_color('border_color'))
        
        if self.widget_type in ['gauge', 'slider', 'toggle', 'button']:
            self.accent_color_btn = QPushButton()
            layout.addRow("Accent Color:", self.accent_color_btn)
            self.accent_color_btn.clicked.connect(lambda: self._choose_color('accent_color'))
        
        if self.widget_type == 'button':
            self.button_bg_color_btn = QPushButton()
            layout.addRow("Button Background Color:", self.button_bg_color_btn)
            self.button_bg_color_btn.clicked.connect(lambda: self._choose_color('button_bg_color'))

        if self.widget_type == 'toggle':
            self.toggle_off_color_btn = QPushButton()
            self.toggle_handle_color_btn = QPushButton()
            layout.addRow("Toggle OFF Color:", self.toggle_off_color_btn)
            layout.addRow("Toggle Handle Color:", self.toggle_handle_color_btn)
            self.toggle_off_color_btn.clicked.connect(lambda: self._choose_color('toggle_off_color'))
            self.toggle_handle_color_btn.clicked.connect(lambda: self._choose_color('toggle_handle_color'))

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        layout.addRow("Font Size:", self.font_size_spin)
        self.font_size_spin.valueChanged.connect(self._emit_config_changed)

        # Icon settings group
        icon_group = QGroupBox("Ikon-innstillinger")
        icon_layout = QFormLayout()

        # Icon picker button
        icon_btn_layout = QHBoxLayout()
        self.icon_display = QLabel("Ingen ikon")
        self.icon_display.setStyleSheet("""
            QLabel {
                background-color: #333333;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: 24px;
                min-width: 60px;
                min-height: 60px;
            }
        """)
        self.icon_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.choose_icon_btn = QPushButton("Velg ikon...")
        self.choose_icon_btn.clicked.connect(self._choose_icon)
        self.clear_icon_btn = QPushButton("Fjern ikon")
        self.clear_icon_btn.clicked.connect(self._clear_icon)
        icon_btn_layout.addWidget(self.icon_display)
        icon_btn_layout.addWidget(self.choose_icon_btn)
        icon_btn_layout.addWidget(self.clear_icon_btn)
        icon_btn_layout.addStretch()
        icon_layout.addRow("Ikon:", icon_btn_layout)

        # Icon size
        self.icon_size_spin = QSpinBox()
        self.icon_size_spin.setRange(8, 128)
        self.icon_size_spin.setValue(24)
        self.icon_size_spin.valueChanged.connect(self._emit_config_changed)
        icon_layout.addRow("Ikonstørrelse (px):", self.icon_size_spin)

        # Icon position
        self.icon_position_combo = QComboBox()
        self.icon_position_combo.addItems(["left", "right", "top", "bottom", "only"])
        self.icon_position_combo.currentTextChanged.connect(self._emit_config_changed)
        icon_layout.addRow("Ikonposisjon:", self.icon_position_combo)

        icon_group.setLayout(icon_layout)
        layout.addRow(icon_group)

        # Opacity slider
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        self.opacity_label = QLabel("100%")
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        layout.addRow("Gjennomsiktighet:", opacity_layout)

    def init_data_tab(self):
        layout = QFormLayout(self.data_tab)
        self.unit = QLineEdit()
        layout.addRow("Unit:", self.unit)
        self.unit.textChanged.connect(self._emit_config_changed)
        
        if self.widget_type in ['gauge', 'gauge_circular', 'gauge_linear', 'gauge_speedometer', 'gauge_voltage']:
            self.min_value_spin = QDoubleSpinBox()
            self.max_value_spin = QDoubleSpinBox()
            self.min_value_spin.setRange(-1000000, 1000000)
            self.max_value_spin.setRange(-1000000, 1000000)
            layout.addRow("Minimum Value:", self.min_value_spin)
            layout.addRow("Maximum Value:", self.max_value_spin)
            self.min_value_spin.valueChanged.connect(self._emit_config_changed)
            self.max_value_spin.valueChanged.connect(self._emit_config_changed)

    def _choose_color(self, color_attr):
        current_color = QColor(self.config.get(color_attr, "#ffffff"))
        color = QColorDialog.getColor(current_color, self, f"Select {color_attr.replace('_', ' ').title()}")
        if color.isValid():
            button = getattr(self, f"{color_attr}_btn", None)
            if button:
                button.setStyleSheet(f"background-color: {color.name()};")
            self.config[color_attr] = color.name()
            self._emit_config_changed()

    def _choose_icon(self):
        """Open icon picker dialog"""
        current_icon = self.config.get('icon_data', '')
        dialog = IconPickerDialog(current_icon, self)
        if dialog.exec():
            icon_data = dialog.get_icon_data()
            self.config['icon_data'] = icon_data['icon']
            self.config['icon_is_text'] = icon_data['is_text']
            self._update_icon_display()
            self._emit_config_changed()

    def _clear_icon(self):
        """Clear selected icon"""
        self.config['icon_data'] = ''
        self.config['icon_is_text'] = False
        self._update_icon_display()
        self._emit_config_changed()

    def _update_icon_display(self):
        """Update the icon display preview"""
        icon_data = self.config.get('icon_data', '')
        is_text = self.config.get('icon_is_text', False)

        if not icon_data:
            self.icon_display.setText("Ingen ikon")
            self.icon_display.setPixmap(QPixmap())
        elif is_text:
            # Display text/emoji icon
            self.icon_display.setText(icon_data)
            self.icon_display.setPixmap(QPixmap())
        else:
            # Display image icon
            self.icon_display.setText("")
            if Path(icon_data).exists():
                pixmap = QPixmap(icon_data)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        48, 48,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.icon_display.setPixmap(scaled)
                else:
                    self.icon_display.setText("❌")
            else:
                self.icon_display.setText("❌")

    def _on_opacity_changed(self, value):
        """Handle opacity slider change"""
        self.opacity_label.setText(f"{value}%")
        self.config['individual_opacity'] = value / 100.0
        self._emit_config_changed()

    def _emit_config_changed(self):
        self.config_changed.emit(self.get_config())
        
    def load_config(self):
        self.display_name_edit.setText(self.config.get('display_name', ''))
        self.show_title.setChecked(self.config.get('show_title', True))
        self.show_text.setChecked(self.config.get('show_text', True))

        theme = self.config.get('theme_selector', 'use_global')
        index = self.theme_selector.findData(theme)
        if index != -1: self.theme_selector.setCurrentIndex(index)

        def load_color(attr, default):
            color = QColor(self.config.get(attr, default))
            if hasattr(self, f"{attr}_btn"):
                getattr(self, f"{attr}_btn").setStyleSheet(f"background-color: {color.name()};")

        load_color('bg_color', '#1F2428')
        load_color('text_color', '#D9D9D9')
        load_color('border_color', '#2F3338')
        if hasattr(self, 'accent_color_btn'): load_color('accent_color', '#0d6efd')
        if hasattr(self, 'button_bg_color_btn'): load_color('button_bg_color', '#343a40')
        if hasattr(self, 'button_text_color_btn'): load_color('button_text_color', '#D9D9D9')
        if hasattr(self, 'toggle_off_color_btn'): load_color('toggle_off_color', '#6c757d')
        if hasattr(self, 'toggle_handle_color_btn'): load_color('toggle_handle_color', '#ffffff')

        self.font_size_spin.setValue(self.config.get('font_size', 12))
        if hasattr(self, 'unit'): self.unit.setText(self.config.get('unit', ''))
        if hasattr(self, 'min_value_spin'): self.min_value_spin.setValue(self.config.get('min_value', 0))
        if hasattr(self, 'max_value_spin'): self.max_value_spin.setValue(self.config.get('max_value', 100))

        # Load icon settings
        if hasattr(self, 'icon_size_spin'):
            self.icon_size_spin.setValue(self.config.get('icon_size', 24))
        if hasattr(self, 'icon_position_combo'):
            icon_pos = self.config.get('icon_position', 'left')
            index = self.icon_position_combo.findText(icon_pos)
            if index != -1: self.icon_position_combo.setCurrentIndex(index)
        if hasattr(self, 'opacity_slider'):
            opacity = self.config.get('individual_opacity', 1.0)
            self.opacity_slider.setValue(int(opacity * 100))
            self.opacity_label.setText(f"{int(opacity * 100)}%")

        # Update icon display
        if hasattr(self, 'icon_display'):
            self._update_icon_display()

    def get_config(self):
        self.config['display_name'] = self.display_name_edit.text()
        self.config['show_title'] = self.show_title.isChecked()
        self.config['show_text'] = self.show_text.isChecked()
        self.config['theme_selector'] = self.theme_selector.currentData()
        self.config['font_size'] = self.font_size_spin.value()
        if hasattr(self, 'unit'): self.config['unit'] = self.unit.text()
        if hasattr(self, 'min_value_spin'): self.config['min_value'] = self.min_value_spin.value()
        if hasattr(self, 'max_value_spin'): self.config['max_value'] = self.max_value_spin.value()

        # Save icon settings
        if hasattr(self, 'icon_size_spin'):
            self.config['icon_size'] = self.icon_size_spin.value()
        if hasattr(self, 'icon_position_combo'):
            self.config['icon_position'] = self.icon_position_combo.currentText()

        # Note: color attributes and icon_data are set directly in their respective methods
        return self.config