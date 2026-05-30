from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QTextEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from updater import AutoUpdater
import requests


class UpdateCheckerThread(QThread):
    """Thread للتحقق من التحديثات"""
    update_found = pyqtSignal(dict)
    no_update = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, updater):
        super().__init__()
        self.updater = updater
    
    def run(self):
        try:
            result = self.updater.check_for_updates()
            if result.get('available'):
                self.update_found.emit(result)
            else:
                self.no_update.emit(result.get('message', 'No updates available'))
        except Exception as e:
            self.error.emit(str(e))


class UpdateDownloaderThread(QThread):
    """Thread لتحميل التحديثات"""
    progress = pyqtSignal(int)
    completed = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, updater, download_url):
        super().__init__()
        self.updater = updater
        self.download_url = download_url
    
    def run(self):
        try:
            def progress_callback(p):
                self.progress.emit(int(p))
            
            result = self.updater.download_update(
                self.download_url,
                progress_callback=progress_callback
            )
            
            if result['success']:
                self.completed.emit(result['file_path'])
            else:
                self.error.emit(result.get('error', 'Download failed'))
        except Exception as e:
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    """نافذة التحديثات"""
    
    def __init__(self, parent=None, auto_check=False):
        super().__init__(parent)
        self.setWindowTitle("Software Updates")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.auto_check = auto_check
        
        self.updater = AutoUpdater()
        self.init_ui()
        
        if auto_check:
            self.check_updates()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # العنوان
        self.title_label = QLabel("Software Updates")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # معلومات الإصدار الحالي
        current_version = self.updater.current_version
        self.version_label = QLabel(f"Current Version: {current_version}")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.version_label)
        
        # منطقة العرض
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("Click 'Check for Updates' to see available updates...")
        layout.addWidget(self.info_text)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # الأزرار
        button_layout = QDialogButtonBox()
        
        self.check_btn = QPushButton("Check for Updates")
        self.check_btn.clicked.connect(self.check_updates)
        button_layout.addButton(self.check_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        self.download_btn = QPushButton("Download & Install")
        self.download_btn.clicked.connect(self.download_update)
        self.download_btn.setEnabled(False)
        button_layout.addButton(self.download_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addButton(self.close_btn, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_layout)
        self.setLayout(layout)
        
        self.update_info = None
    
    def check_updates(self):
        """التحقق من التحديثات"""
        self.check_btn.setEnabled(False)
        self.info_text.setPlainText("Checking for updates...")
        
        self.checker_thread = UpdateCheckerThread(self.updater)
        self.checker_thread.update_found.connect(self.on_update_found)
        self.checker_thread.no_update.connect(self.on_no_update)
        self.checker_thread.error.connect(self.on_error)
        self.checker_thread.start()
    
    def on_update_found(self, result):
        """عند العثور على تحديث"""
        self.update_info = result
        self.check_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        
        info = f"""
New Version Available: {result['latest_version']}

Release Notes:
{result.get('release_notes', 'No release notes available')}

Published: {result.get('published_at', 'Unknown')}
        """
        self.info_text.setPlainText(info)
    
    def on_no_update(self, message):
        """عند عدم وجود تحديثات"""
        self.check_btn.setEnabled(True)
        self.info_text.setPlainText(f"✓ {message}\n\nYou are running the latest version.")
        
        if self.auto_check:
            self.close()
    
    def on_error(self, error):
        """عند حدوث خطأ"""
        self.check_btn.setEnabled(True)
        self.info_text.setPlainText(f"✗ Error: {error}")
    
    def download_update(self):
        """تحميل التحديث"""
        if not self.update_info or not self.update_info.get('download_url'):
            return
        
        reply = QMessageBox.question(
            self,
            "Download Update",
            f"This will download and install version {self.update_info['latest_version']}.\n"
            "The application will restart after installation.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.download_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.info_text.setPlainText("Downloading update...")
        
        self.downloader_thread = UpdateDownloaderThread(
            self.updater,
            self.update_info['download_url']
        )
        self.downloader_thread.progress.connect(self.on_download_progress)
        self.downloader_thread.completed.connect(self.on_download_completed)
        self.downloader_thread.error.connect(self.on_download_error)
        self.downloader_thread.start()
    
    def on_download_progress(self, progress):
        """تحديث شريط التقدم"""
        self.progress_bar.setValue(progress)
        self.info_text.setPlainText(f"Downloading... {progress}%")
    
    def on_download_completed(self, file_path):
        """عند اكتمال التحميل"""
        self.info_text.setPlainText("Download complete! Installing update...")
        
        # تطبيق التحديث
        result = self.updater.apply_update(file_path)
        
        if result.get('success'):
            self.updater.update_version(self.update_info['latest_version'])
            QMessageBox.information(
                self,
                "Update Successful",
                "Update installed successfully!\nThe application will now restart."
            )
            # البرنامج سيُغلق تلقائياً من apply_update
        else:
            QMessageBox.critical(
                self,
                "Update Failed",
                f"Failed to install update:\n{result.get('error', 'Unknown error')}"
            )
            self.download_btn.setEnabled(True)
            self.check_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_download_error(self, error):
        """عند فشل التحميل"""
        QMessageBox.critical(
            self,
            "Download Failed",
            f"Failed to download update:\n{error}"
        )
        self.download_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        self.progress_bar.setVisible(False)