from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QTextEdit, QDoubleSpinBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush
from database import Session
from models import Deal, Customer


class DealDialog(QDialog):
    """نافذة إضافة/تعديل صفقة"""
    
    def __init__(self, parent=None, deal=None, session=None):
        super().__init__(parent)
        self.deal = deal
        self.session = session
        self.setWindowTitle("Add Deal" if not deal else "Edit Deal")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        self.title_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.value_input = QDoubleSpinBox()
        self.value_input.setMaximum(999999999)
        self.value_input.setPrefix("$ ")
        self.stage_combo = QComboBox()
        self.stage_combo.addItems([
            "prospecting", "qualification", "proposal",
            "negotiation", "won", "lost"
        ])
        self.probability_combo = QComboBox()
        [self.probability_combo.addItem(f"{i}%") for i in range(0, 101, 10)]
        self.expected_close_input = QDateEdit()
        self.expected_close_input.setCalendarPopup(True)
        self.expected_close_input.setDate(QDate.currentDate().addMonths(1))
        self.customer_combo = QComboBox()
        for c in session.query(Customer).all():
            self.customer_combo.addItem(c.name, c.id)
        
        layout.addRow("Title*:", self.title_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Customer*:", self.customer_combo)
        layout.addRow("Value:", self.value_input)
        layout.addRow("Stage:", self.stage_combo)
        layout.addRow("Probability:", self.probability_combo)
        layout.addRow("Expected Close:", self.expected_close_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        
        if deal:
            self.title_input.setText(deal.title)
            self.description_input.setText(deal.description or "")
            self.value_input.setValue(deal.value or 0)
            self.stage_combo.setCurrentText(deal.stage)
            self.probability_combo.setCurrentText(f"{deal.probability}%")
            self.expected_close_input.setDate(
                QDate.fromString(str(deal.expected_close), "yyyy-MM-dd")
            ) if deal.expected_close else None
            for i in range(self.customer_combo.count()):
                if self.customer_combo.itemData(i) == deal.customer_id:
                    self.customer_combo.setCurrentIndex(i)
                    break
    
    def get_data(self):
        return {
            'title': self.title_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'customer_id': self.customer_combo.currentData(),
            'value': self.value_input.value(),
            'stage': self.stage_combo.currentText(),
            'probability': int(self.probability_combo.currentText().replace('%', '')),
            'expected_close': self.expected_close_input.date().toPyDate()
        }


class DealsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        # أزرار التحكم (نفس ترتيب customers.py بالضبط)
        controls_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by deal, customer...")
        self.search_input.textChanged.connect(self.filter_data)
        controls_layout.addWidget(self.search_input)
        
        self.stage_filter = QComboBox()
        self.stage_filter.addItems([
            "All", "Prospecting", "Qualification", "Proposal",
            "Negotiation", "Won", "Lost"
        ])
        self.stage_filter.currentIndexChanged.connect(self.filter_data)
        controls_layout.addWidget(self.stage_filter)
        
        self.add_btn = QPushButton("Add Deal")
        self.add_btn.clicked.connect(self.add_deal)
        controls_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_deal)
        controls_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_deal)
        controls_layout.addWidget(self.delete_btn)
        
        # جدول الصفقات (بنفس إعدادات جدول customers.py)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Deal", "Customer", "Value", "Stage", "Probability", "Expected Close"
        ])
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_deal)
        self.table.setColumnHidden(0, True)  # إخفاء عمود ID
        
        # ترتيب الواجهة
        main_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)
    
    def load_data(self):
        deals = self.session.query(Deal).all()
        self.table.setRowCount(len(deals))
        
        for row, deal in enumerate(deals):
            self.table.setItem(row, 0, QTableWidgetItem(str(deal.id)))
            self.table.setItem(row, 1, QTableWidgetItem(deal.title))
            
            customer_name = deal.customer.name if deal.customer else "No Customer"
            self.table.setItem(row, 2, QTableWidgetItem(customer_name))
            
            value_item = QTableWidgetItem(f"${deal.value:,.2f}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, value_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(deal.stage))
            
            prob_item = QTableWidgetItem(f"{deal.probability}%")
            prob_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, prob_item)
            
            date_str = deal.expected_close.strftime("%Y-%m-%d") if deal.expected_close else "N/A"
            self.table.setItem(row, 6, QTableWidgetItem(date_str))
            
            # تلوين الصف حسب المرحلة
            color = self._get_stage_color(deal.stage)
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setForeground(QBrush(QColor("#ffffff")))
    
    def _get_stage_color(self, stage):
        colors = {
            'prospecting': '#e6f7ff',
            'qualification': '#e6f7ff',
            'proposal': '#e6f7ff',
            'negotiation': '#e6f7ff',
            'won': '#e6ffe6',
            'lost': '#ffe6e6'
        }
        return colors.get(stage, '#f0f0f0')
    
    def filter_data(self):
        search_text = self.search_input.text().lower()
        stage_filter = self.stage_filter.currentText()
        
        for row in range(self.table.rowCount()):
            title = self.table.item(row, 1).text().lower()
            customer = self.table.item(row, 2).text().lower()
            stage = self.table.item(row, 4).text()
            
            show = True
            if search_text and search_text not in title and search_text not in customer:
                show = False
            
            if stage_filter != "All" and stage != stage_filter.lower():
                show = False
            
            self.table.setRowHidden(row, not show)
    
    def add_deal(self):
        # التحقق من وجود عملاء أولاً
        if self.session.query(Customer).count() == 0:
            QMessageBox.warning(
                self, "No Customers",
                "You must add at least one customer first!"
            )
            return
        
        dialog = DealDialog(self, session=self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            if not data['title']:
                QMessageBox.warning(self, "Error", "Title is required!")
                return
            
            deal = Deal(**data)
            self.session.add(deal)
            self.session.commit()
            
            QMessageBox.information(self, "Success", "Deal added successfully!")
            self.load_data()
    
    def edit_deal(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Edit", "Please select a deal to edit")
            return
        
        deal_id = int(self.table.item(selected, 0).text())
        deal = self.session.get(Deal, deal_id)
        
        dialog = DealDialog(self, deal=deal, session=self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            for key, value in data.items():
                setattr(deal, key, value)
            
            self.session.commit()
            QMessageBox.information(self, "Success", "Deal updated successfully!")
            self.load_data()
    
    def delete_deal(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Delete", "Please select a deal to delete")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Deal",
            "Are you sure you want to delete this deal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deal_id = int(self.table.item(selected, 0).text())
            deal = self.session.get(Deal, deal_id)
            self.session.delete(deal)
            self.session.commit()
            
            QMessageBox.information(self, "Success", "Deal deleted successfully!")
            self.load_data()