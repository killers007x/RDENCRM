from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QGroupBox,
    QFormLayout, QFileDialog, QCheckBox
)
import shutil
import os
from datetime import datetime


class SettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("<h2 style='margin:0;'>⚙️ Settings</h2>")
        layout.addWidget(title)
        
        # Backup group
        backup_group = QGroupBox("💾 Database Backup & Restore")
        backup_layout = QVBoxLayout()
        
        backup_btn = QPushButton("Create Backup")
        backup_btn.clicked.connect(self.create_backup)
        backup_layout.addWidget(backup_btn)
        
        restore_btn = QPushButton("Restore from Backup")
        restore_btn.clicked.connect(self.restore_backup)
        backup_layout.addWidget(restore_btn)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # App info
        info_group = QGroupBox("ℹ️ Application Info")
        info_layout = QFormLayout()
        info_layout.addRow("Version:", QLabel("1.0.0"))
        info_layout.addRow("Database:", QLabel("SQLite (crm.db)"))
        info_layout.addRow("License:", QLabel("Commercial"))
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_backup(self):
        source = "crm.db"
        if not os.path.exists(source):
            QMessageBox.warning(self, "Error", "Database not found.")
            return
        
        default_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        dest, _ = QFileDialog.getSaveFileName(self, "Save Backup", default_name, "Database (*.db)")
        
        if dest:
            try:
                shutil.copy2(source, dest)
                QMessageBox.information(self, "Success", f"✅ Backup created:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def restore_backup(self):
        reply = QMessageBox.warning(
            self, "Warning", "This will replace your current database. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        source, _ = QFileDialog.getOpenFileName(self, "Select Backup", "", "Database (*.db)")
        if source:
            try:
                shutil.copy2(source, "crm.db")
                QMessageBox.information(self, "Success", "✅ Database restored. Please restart the application.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))