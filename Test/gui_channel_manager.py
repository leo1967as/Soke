import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QLabel, 
                             QMessageBox, QFrame)
from PySide6.QtCore import Qt
from discord_utils import DiscordManager

class ChannelManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Channel Manager - Sokeber")
        self.resize(500, 350)
        
        # Setup Backend
        self.token_path = r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token"
        self.guild_id = "1475450344334037063"
        self.manager = DiscordManager(self.token_path)
        
        # State
        self.channels = []
        self.categories = []
        
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Style
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 14px; font-weight: bold; }
            QComboBox { 
                background-color: #313244; 
                color: #cdd6f4; 
                border: 1px solid #45475a; 
                padding: 8px; 
                border-radius: 5px;
                min-height: 30px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton#refresh_btn { background-color: #a6e3a1; }
            QPushButton#refresh_btn:hover { background-color: #94e2d5; }
        """)

        # Header
        header = QLabel("Discord Channel Management")
        header.setStyleSheet("font-size: 20px; color: #89b4fa; margin-bottom: 10px;")
        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

        # Selector Area
        form_layout = QVBoxLayout()
        
        # Source Channel
        form_layout.addWidget(QLabel("Select Channel to Move:"))
        self.channel_box = QComboBox()
        form_layout.addWidget(self.channel_box)

        form_layout.addSpacing(10)

        # Destination Category
        form_layout.addWidget(QLabel("Select Destination Category:"))
        self.category_box = QComboBox()
        form_layout.addWidget(self.category_box)

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.move_btn = QPushButton("🚀 Move Channel")
        self.move_btn.clicked.connect(self.handle_move)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("refresh_btn")
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.move_btn)
        
        layout.addLayout(btn_layout)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #6c7086; font-size: 12px; font-style: italic;")
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def refresh_data(self):
        try:
            self.status_label.setText("Fetching channels...")
            all_channels = self.manager.get_channels(self.guild_id)
            
            self.channels = [c for c in all_channels if c['type'] != 4] # Not categories
            self.categories = [c for c in all_channels if c['type'] == 4] # Only categories
            
            # Update Boxes
            self.channel_box.clear()
            for c in self.channels:
                self.channel_box.addItem(f"{c['name']} ({'Voice' if c['type']==2 else 'Text'})", c['id'])
                
            self.category_box.clear()
            self.category_box.addItem("None (No Category)", None)
            for cat in self.categories:
                self.category_box.addItem(cat['name'], cat['id'])
                
            self.status_label.setText(f"Loaded {len(self.channels)} channels and {len(self.categories)} categories.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {str(e)}")

    def handle_move(self):
        channel_id = self.channel_box.currentData()
        category_id = self.category_box.currentData()
        channel_name = self.channel_box.currentText()
        category_name = self.category_box.currentText()
        
        if not channel_id:
            return

        confirm = QMessageBox.question(self, "Confirm Move", 
                                     f"Move '{channel_name}' to '{category_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            success, msg = self.manager.move_channel(channel_id, category_id)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Failed", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChannelManagerGUI()
    window.show()
    sys.exit(app.exec())
