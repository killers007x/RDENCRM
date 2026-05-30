from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QTextEdit, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from database import Session
from models import Task, Customer


class TaskDialog(QDialog):
    """نافذة إضافة/تعديل مهمة"""
    
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task
        self.session = Session()
        self.setWindowTitle("Add Task" if not task else "Edit Task")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        self.title_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("No Customer", None)
        for c in self.session.query(Customer).all():
            self.customer_combo.addItem(c.name, c.id)
            
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addDays(7))
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["low", "medium", "high"])
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pending", "in_progress", "completed"])
        
        layout.addRow("Title*:", self.title_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Customer:", self.customer_combo)
        layout.addRow("Due Date:", self.due_date_input)
        layout.addRow("Priority:", self.priority_combo)
        layout.addRow("Status:", self.status_combo)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        
        if task:
            self.title_input.setText(task.title)
            self.description_input.setText(task.description or "")
            self.due_date_input.setDate(
                QDate.fromString(str(task.due_date), "yyyy-MM-dd")
            ) if task.due_date else None
            self.priority_combo.setCurrentText(task.priority)
            self.status_combo.setCurrentText(task.status)
            
            for i in range(self.customer_combo.count()):
                if self.customer_combo.itemData(i) == task.customer_id:
                    self.customer_combo.setCurrentIndex(i)
                    break
    
    def get_data(self):
        return {
            'title': self.title_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'customer_id': self.customer_combo.currentData(),
            'due_date': self.due_date_input.date().toPyDate(),
            'priority': self.priority_combo.currentText(),
            'status': self.status_combo.currentText()
        }


class TasksTab(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        # أزرار التحكم والفلاتر (بنفس ترتيب customers.py)
        controls_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, customer...")
        self.search_input.textChanged.connect(self.filter_data)
        controls_layout.addWidget(self.search_input)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "pending", "in_progress", "completed"])
        self.status_filter.currentIndexChanged.connect(self.filter_data)
        controls_layout.addWidget(self.status_filter)
        
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All", "low", "medium", "high"])
        self.priority_filter.currentIndexChanged.connect(self.filter_data)
        controls_layout.addWidget(self.priority_filter)
        
        self.add_btn = QPushButton("Add Task")
        self.add_btn.clicked.connect(self.add_task)
        controls_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_task)
        controls_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_task)
        controls_layout.addWidget(self.delete_btn)
        
        # جدول المهام (بنفس إعدادات جدول customers.py)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Title", "Customer", "Due Date", "Priority", "Status", "Description"
        ])
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_task)
        self.table.setColumnHidden(0, True)  # إخفاء عمود ID
        
        # ترتيب الواجهة
        main_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

    def load_data(self):
        tasks = self.session.query(Task).all()
        
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            self.table.setItem(row, 0, QTableWidgetItem(str(task.id)))
            self.table.setItem(row, 1, QTableWidgetItem(task.title))
            
            customer_name = task.customer.name if task.customer else "No Customer"
            self.table.setItem(row, 2, QTableWidgetItem(customer_name))
            
            date_str = task.due_date.strftime("%Y-%m-%d") if task.due_date else "N/A"
            self.table.setItem(row, 3, QTableWidgetItem(date_str))
            
            self.table.setItem(row, 4, QTableWidgetItem(task.priority))
            self.table.setItem(row, 5, QTableWidgetItem(task.status))
            self.table.setItem(row, 6, QTableWidgetItem(task.description or ""))

    def filter_data(self):
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()
        priority_filter = self.priority_filter.currentText()
        
        for row in range(self.table.rowCount()):
            title = self.table.item(row, 1).text().lower()
            customer = self.table.item(row, 2).text().lower()
            status = self.table.item(row, 5).text()
            priority = self.table.item(row, 4).text()
            
            show = True
            if search_text and search_text not in title and search_text not in customer:
                show = False
            
            if status_filter != "All" and status != status_filter:
                show = False
                
            if priority_filter != "All" and priority != priority_filter:
                show = False
            
            self.table.setRowHidden(row, not show)

    def add_task(self):
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            if not data['title']:
                QMessageBox.warning(self, "Error", "Title is required!")
                return
            
            task = Task(**data)
            self.session.add(task)
            self.session.commit()
            
            QMessageBox.information(self, "Success", "Task added successfully!")
            self.load_data()

    def edit_task(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Edit", "Please select a task to edit")
            return
        
        task_id = int(self.table.item(selected, 0).text())
        task = self.session.get(Task, task_id)
        
        dialog = TaskDialog(self, task)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            for key, value in data.items():
                setattr(task, key, value)
            
            self.session.commit()
            QMessageBox.information(self, "Success", "Task updated successfully!")
            self.load_data()

    def delete_task(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Delete", "Please select a task to delete")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Task",
            "Are you sure you want to delete this task?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            task_id = int(self.table.item(selected, 0).text())
            task = self.session.get(Task, task_id)
            self.session.delete(task)
            self.session.commit()
            
            QMessageBox.information(self, "Success", "Task deleted successfully!")
            self.load_data()