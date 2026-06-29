import os
import sys
import json
import hashlib
import platform
import uuid
import base64
import time
import stat
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFileDialog, QHBoxLayout, QGroupBox
)
from PyQt6.QtCore import Qt
from cryptography.fernet import Fernet

# 🔑 مفتاح التشفير (غيّره قبل التوزيع التجاري)
SECRET_SALT = "CRM_Pro_Commercial_2026_SecretKey"
_key_material = hashlib.sha256(SECRET_SALT.encode()).digest()
_fixed_key = base64.urlsafe_b64encode(_key_material)
_cipher = Fernet(_fixed_key)

# المجلد المخفي للبيانات الحساسة
LICENSE_DIR = Path.home() / ".crm_pro_data"
LICENSE_FILE = LICENSE_DIR / "license.dat"
SFO_BACKUP_FILE = LICENSE_DIR / "device_backup.sfo"
INIT_MARKER = LICENSE_DIR / ".crm_initialized"

# المجلد الذي يعمل منه البرنامج (بجانب main.py أو exe)
APP_DIR = Path(sys.argv[0]).parent if sys.argv[0] else Path.cwd()
RECOVERY_FILE = APP_DIR / "license_recovery.txt"

def get_device_id() -> str:
    raw = f"{platform.node()}{platform.machine()}{uuid.getnode()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def _safe_write_file(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        except:
            pass
        try:
            path.unlink()
        except:
            pass
    temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(temp_fd, 'wb') as tmp_f:
            tmp_f.write(content)
        os.replace(temp_path, path)
    except:
        os.close(temp_fd)
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    if os.name == 'nt':
        os.system(f'attrib +h "{path}" >nul 2>&1')

def _encrypt_license_data(data: dict) -> bytes:
    return _cipher.encrypt(json.dumps(data, separators=(',', ':')).encode('utf-8'))

def _decrypt_license_data(raw_bytes: bytes) -> Optional[dict]:
    try:
        return json.loads(_cipher.decrypt(raw_bytes).decode('utf-8'))
    except:
        return None

def _encrypt_id_for_sfo(device_id: str) -> str:
    key_bytes = SECRET_SALT.encode()
    encrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(device_id.encode())])
    return base64.b64encode(encrypted).decode()

def _decrypt_id_from_sfo(encrypted_str: str) -> Optional[str]:
    try:
        key_bytes = SECRET_SALT.encode()
        decrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(base64.b64decode(encrypted_str))])
        return decrypted.decode()
    except:
        return None

def create_license_files(device_id: str, activated: bool = True):
    LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    license_data = {
        "device_id": device_id,
        "activated": activated,
        "created_at": platform.node(),
        "timestamp": str(int(time.time()))
    }
    _safe_write_file(LICENSE_FILE, _encrypt_license_data(license_data))
    sfo_data = {
        "format": "SFO_BACKUP",
        "version": 1,
        "encrypted_device_id": _encrypt_id_for_sfo(device_id),
        "checksum": hashlib.sha256(device_id.encode()).hexdigest()
    }
    with open(SFO_BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(sfo_data, f, indent=2)
    INIT_MARKER.touch()
    if os.name == 'nt':
        os.system(f'attrib +h "{INIT_MARKER}" >nul 2>&1')

def read_license() -> Optional[dict]:
    if not LICENSE_FILE.exists():
        return None
    try:
        with open(LICENSE_FILE, 'rb') as f:
            return _decrypt_license_data(f.read())
    except:
        return None

def update_license_status(activated: bool):
    data = read_license()
    if data is None:
        return
    data["activated"] = activated
    data["last_updated"] = str(int(time.time()))
    _safe_write_file(LICENSE_FILE, _encrypt_license_data(data))

def _create_recovery_file(device_id: str):
    """إنشاء ملف استرداد الترخيص في مجلد البرنامج."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    user_path = str(Path.home())  # المسار الحقيقي للمستخدم
    content = (
        "Your license files are missing or corrupted.\n"
        "\n"
        "To restore your license, please follow these steps:\n"
        "\n"
        "1. Visit the official recovery repository:\n"
        "   https://github.com/killers007x/RdenCRM_backup\n"
        "\n"
        "go to this path\n"
        "\n"
        f"{user_path}\n"
        "\n"
        "create a folder and name it \".crm_pro_data\" and put all the files after extract\n"
    )
    with open(RECOVERY_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

def check_license() -> Tuple[bool, str, Optional[str]]:
    current_id = get_device_id()
    if not LICENSE_FILE.exists():
        _create_recovery_file(current_id)
        return False, current_id, (
            "License file is missing.\n\n"
            "A recovery guide has been saved next to the program:\n"
            f"{RECOVERY_FILE}"
        )
    data = read_license()
    if data is None:
        _create_recovery_file(current_id)
        return False, current_id, (
            "License file is corrupted.\n\n"
            "A recovery guide has been saved next to the program:\n"
            f"{RECOVERY_FILE}"
        )
    if data.get("device_id") != current_id:
        _create_recovery_file(current_id)
        return False, current_id, (
            "License is tied to another device.\n\n"
            "A recovery guide has been saved next to the program:\n"
            f"{RECOVERY_FILE}"
        )
    return True, current_id, None

def verify_activation_code(code: str) -> bool:
    current_id = get_device_id()
    expected = hashlib.sha256((current_id + SECRET_SALT).encode()).hexdigest()[:16]
    return code.strip().upper().replace("-", "") == expected.upper()

def import_sfo_file(file_path: str) -> Tuple[bool, str]:
    current_id = get_device_id()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sfo = json.load(f)
        if sfo.get("format") != "SFO_BACKUP":
            return False, "Invalid SFO file format."
        decrypted_id = _decrypt_id_from_sfo(sfo.get("encrypted_device_id", ""))
        if not decrypted_id:
            return False, "Failed to decrypt device ID."
        if hashlib.sha256(decrypted_id.encode()).hexdigest() != sfo.get("checksum"):
            return False, "SFO integrity check failed."
        if decrypted_id != current_id:
            return False, "SFO file belongs to a different device."
        create_license_files(current_id, activated=True)
        return True, ""
    except Exception as e:
        return False, f"Error reading SFO file: {str(e)}"

class ActivationDialog(QDialog):
    def __init__(self, device_id: str, reason: str, expected_path: str):
        super().__init__()
        self.setWindowTitle("License Verification Required")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        lay = QVBoxLayout()
        lay.addWidget(QLabel("<b>License Files Missing or Invalid</b>"))
        lay.addWidget(QLabel(reason))
        lay.addWidget(QLabel(f"Recovery guide saved at: <code>{expected_path}</code>"))
        code_grp = QGroupBox("Activate with Code")
        code_lay = QVBoxLayout()
        code_lay.addWidget(QLabel("Enter the activation code:"))
        self.code_in = QLineEdit()
        self.code_in.setPlaceholderText("e.g., A1B2-C3D4-E5F6-G7H8")
        code_lay.addWidget(self.code_in)
        btn_code = QPushButton("Verify & Activate")
        btn_code.clicked.connect(self._handle_code)
        code_lay.addWidget(btn_code)
        code_grp.setLayout(code_lay)
        lay.addWidget(code_grp)
        sfo_grp = QGroupBox("Activate with Backup")
        sfo_lay = QVBoxLayout()
        sfo_lay.addWidget(QLabel("Import your .sfo backup file:"))
        btn_lay = QHBoxLayout()
        self.sfo_lbl = QLabel("No file selected")
        btn_lay.addWidget(self.sfo_lbl)
        btn_browse = QPushButton("Browse .sfo")
        btn_browse.clicked.connect(self._browse_sfo)
        btn_lay.addWidget(btn_browse)
        btn_import = QPushButton("Import & Activate")
        btn_import.clicked.connect(self._handle_sfo)
        btn_lay.addWidget(btn_import)
        sfo_lay.addLayout(btn_lay)
        sfo_grp.setLayout(sfo_lay)
        lay.addWidget(sfo_grp)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        lay.addWidget(self.status)
        btn_close = QPushButton("Close Program")
        btn_close.clicked.connect(self.reject)
        lay.addWidget(btn_close)
        self.setLayout(lay)
        self.selected_sfo = ""

    def _handle_code(self):
        if verify_activation_code(self.code_in.text()):
            create_license_files(get_device_id(), activated=True)
            QMessageBox.information(self, "Success", "Program activated successfully.")
            self.accept()
        else:
            self.status.setText("<font color='red'>Invalid activation code.</font>")

    def _browse_sfo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select SFO", "", "SFO Files (*.sfo);;All Files (*)")
        if path:
            self.selected_sfo = path
            self.sfo_lbl.setText(path)

    def _handle_sfo(self):
        if not self.selected_sfo:
            return
        ok, err = import_sfo_file(self.selected_sfo)
        if ok:
            QMessageBox.information(self, "Success", "Backup imported. Program activated.")
            self.accept()
        else:
            self.status.setText(f"<font color='red'>Import failed: {err}</font>")