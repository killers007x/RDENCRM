import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import Qt

# استيراد جميع التبويبات
from customers import CustomersTab
from deals import DealsTab
from tasks import TasksTab
from dashboard import DashboardTab

from database import init_db

class CRMApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRM Pro - Desktop Application")
        self.setGeometry(100, 100, 1200, 700)
        
        # تهيئة قاعدة البيانات
        init_db()
        
        # إنشاء التبويبات
        tabs = QTabWidget()
        
        self.dashboard_tab = DashboardTab()
        self.customers_tab = CustomersTab()
        self.deals_tab = DealsTab()
        self.tasks_tab = TasksTab()
        
        tabs.addTab(self.dashboard_tab, "Dashboard")
        tabs.addTab(self.customers_tab, "Customers")
        tabs.addTab(self.deals_tab, "Pipeline")
        tabs.addTab(self.tasks_tab, "Tasks")
        
        self.setCentralWidget(tabs)

def main():
    app = QApplication(sys.argv)
    window = CRMApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()