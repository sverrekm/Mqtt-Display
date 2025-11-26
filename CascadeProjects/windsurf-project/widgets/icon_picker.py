from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QPushButton, QLineEdit, QDialogButtonBox,
                             QFileDialog, QGridLayout, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from pathlib import Path

class IconPickerDialog(QDialog):
    """Dialog for selecting icons from file or icon library"""

    # Built-in icon library (Unicode symbols and common icons)
    ICON_LIBRARY = {
        # Basic shapes
        "Circle": "●",
        "Square": "■",
        "Triangle": "▲",
        "Star": "★",
        "Heart": "♥",
        "Diamond": "♦",

        # Arrows
        "Arrow Up": "▲",
        "Arrow Down": "▼",
        "Arrow Left": "◄",
        "Arrow Right": "►",
        "Arrow Up-Down": "↕",
        "Arrow Left-Right": "↔",

        # Symbols
        "Check": "✓",
        "Cross": "✗",
        "Plus": "+",
        "Minus": "−",
        "Warning": "⚠",
        "Info": "ℹ",
        "Gear": "⚙",
        "Home": "🏠",
        "Power": "⏻",
        "Light": "💡",
        "Battery": "🔋",

        # Weather
        "Sun": "☀",
        "Cloud": "☁",
        "Rain": "🌧",
        "Snow": "❄",
        "Thunder": "⚡",
        "Wind": "🌬",

        # Temperature
        "Thermometer": "🌡",
        "Hot": "🔥",
        "Cold": "❄",

        # Numbers
        "0": "0",
        "1": "1",
        "2": "2",
        "3": "3",
        "4": "4",
        "5": "5",
        "6": "6",
        "7": "7",
        "8": "8",
        "9": "9",
    }

    def __init__(self, current_icon_path="", parent=None):
        super().__init__(parent)
        self.current_icon_path = current_icon_path
        self.selected_icon = current_icon_path
        self.is_text_icon = False  # True if icon is from library (text), False if file

        self.setWindowTitle("Velg Ikon")
        self.setMinimumSize(500, 400)

        self.apply_dark_theme()
        self.init_ui()

    def apply_dark_theme(self):
        """Apply dark theme to dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #555555;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #404040;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QFrame {
                background-color: #404040;
                border: 2px solid transparent;
                border-radius: 4px;
            }
            QFrame:hover {
                border: 2px solid #0078d4;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Create tabs
        tabs = QTabWidget()

        # File tab
        file_tab = QWidget()
        self.init_file_tab(file_tab)
        tabs.addTab(file_tab, "Fra fil")

        # Icon library tab
        library_tab = QWidget()
        self.init_library_tab(library_tab)
        tabs.addTab(library_tab, "Ikon-bibliotek")

        layout.addWidget(tabs)

        # Preview section
        preview_group = QFrame()
        preview_layout = QVBoxLayout(preview_group)
        preview_label = QLabel("Forhåndsvisning:")
        self.preview_icon = QLabel()
        self.preview_icon.setMinimumSize(64, 64)
        self.preview_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_icon.setStyleSheet("""
            QLabel {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 48px;
            }
        """)
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(preview_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Load current icon if any
        if self.current_icon_path:
            self.update_preview(self.current_icon_path, False)

    def init_file_tab(self, tab):
        layout = QVBoxLayout(tab)

        # File path input
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Velg en ikon-fil...")
        self.file_path_edit.setText(self.current_icon_path if not self.is_text_icon else "")
        self.file_path_edit.textChanged.connect(lambda text: self.update_preview(text, False))

        browse_btn = QPushButton("Bla gjennom...")
        browse_btn.clicked.connect(self.browse_file)

        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # Info label
        info_label = QLabel(
            "Støttede formater: PNG, JPG, JPEG, BMP, SVG\n"
            "Anbefalt størrelse: 16x16 til 128x128 piksler"
        )
        info_label.setStyleSheet("color: #999999; font-size: 11px;")
        layout.addWidget(info_label)

        layout.addStretch()

    def init_library_tab(self, tab):
        layout = QVBoxLayout(tab)

        # Scroll area for icons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }
        """)

        # Container for icon grid
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(8)

        # Create icon buttons
        row = 0
        col = 0
        for name, symbol in self.ICON_LIBRARY.items():
            icon_btn = self.create_icon_button(name, symbol)
            grid.addWidget(icon_btn, row, col)

            col += 1
            if col >= 6:  # 6 icons per row
                col = 0
                row += 1

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def create_icon_button(self, name, symbol):
        """Create a button for an icon in the library"""
        btn = QPushButton()
        btn.setFixedSize(70, 70)
        btn.setToolTip(name)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 4px;
                font-size: 32px;
                padding: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #0078d4;
                background-color: #4a4a4a;
            }}
        """)
        btn.setText(symbol)
        btn.clicked.connect(lambda: self.select_library_icon(symbol))
        return btn

    def browse_file(self):
        """Open file dialog to select icon file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Velg ikon-fil",
            "",
            "Bildefiler (*.png *.jpg *.jpeg *.bmp *.svg);;Alle filer (*)"
        )

        if file_path:
            self.file_path_edit.setText(file_path)
            self.update_preview(file_path, False)

    def select_library_icon(self, symbol):
        """Select an icon from the library"""
        self.selected_icon = symbol
        self.is_text_icon = True
        self.update_preview(symbol, True)

    def update_preview(self, icon_data, is_text):
        """Update the preview icon"""
        self.selected_icon = icon_data
        self.is_text_icon = is_text

        if is_text:
            # Display text icon
            self.preview_icon.setPixmap(QPixmap())
            self.preview_icon.setText(icon_data)
        else:
            # Display image icon
            self.preview_icon.setText("")
            if icon_data and Path(icon_data).exists():
                pixmap = QPixmap(icon_data)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        64, 64,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.preview_icon.setPixmap(scaled)
                else:
                    self.preview_icon.setText("❌")
            else:
                self.preview_icon.setText("❌" if icon_data else "")

    def get_icon_data(self):
        """Return the selected icon data and type"""
        return {
            'icon': self.selected_icon,
            'is_text': self.is_text_icon
        }
