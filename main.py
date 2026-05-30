import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import Qt
from customers import CustomersTab
from deals import DealsTab
from tasks import TasksTab
from dashboard import DashboardTab
from database import init_db

class CRMApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRM Pro - Desktop")
        self.setGeometry(200, 150, 1050, 620)
        self.setMinimumSize(850, 500)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint | Qt.WindowType.WindowCloseButtonHint)
        init_db()
        tabs = QTabWidget()
        tabs.addTab(DashboardTab(), "Dashboard")
        tabs.addTab(CustomersTab(), "Customers")
        tabs.addTab(DealsTab(), "Pipeline")
        tabs.addTab(TasksTab(), "Tasks")
        self.setCentralWidget(tabs)

def main():
    app = QApplication(sys.argv)
    window = CRMApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()