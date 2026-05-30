import sys
import os
import hashlib
from pathlib import Path


class ProtectionSystem:
    @staticmethod
    def check_debugger():
        try:
            if os.environ.get('DEBUG') or os.environ.get('PYCHARM_HOSTED'):
                return True
            debuggers = ['pdb', 'pydevd', 'pydevd_pycharm']
            for debugger in debuggers:
                if debugger in sys.modules:
                    return True
            return False
        except:
            return False
    
    @staticmethod
    def verify_integrity():
        try:
            # ✅ تم تعديل القائمة لتطابق أسماء ملفاتك الحقيقية بالضبط
            critical_files = [
                'main.py',
                'models.py',
                'database.py',
                'license_manager.py',
                'customers.py',
                'deals.py'
            ]
            for filename in critical_files:
                if not Path(filename).exists():
                    return False
            return True
        except:
            return False
    
    @staticmethod
    def protect():
        if ProtectionSystem.check_debugger():
            print("Warning: Debugger detected")
        if not ProtectionSystem.verify_integrity():
            print("Error: Application integrity check failed")
            return False
        return True