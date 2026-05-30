from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QTextEdit, QDateEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from database import Session
from models import Customer, Deal, Task
from datetime import datetime


class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        title = QLabel("📈 Reports & Analytics")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # أزرار التقارير
        buttons_layout = QHBoxLayout()
        
        self.customers_report_btn = QPushButton("👥 Customers Report")
        self.customers_report_btn.setStyleSheet("padding: 10px; background-color: #007bff; color: white;")
        self.customers_report_btn.clicked.connect(self.generate_customers_report)
        buttons_layout.addWidget(self.customers_report_btn)
        
        self.deals_report_btn = QPushButton("💼 Deals Report")
        self.deals_report_btn.setStyleSheet("padding: 10px; background-color: #28a745; color: white;")
        self.deals_report_btn.clicked.connect(self.generate_deals_report)
        buttons_layout.addWidget(self.deals_report_btn)
        
        self.tasks_report_btn = QPushButton("✅ Tasks Report")
        self.tasks_report_btn.setStyleSheet("padding: 10px; background-color: #dc3545; color: white;")
        self.tasks_report_btn.clicked.connect(self.generate_tasks_report)
        buttons_layout.addWidget(self.tasks_report_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # منطقة العرض
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setFont(QFont("Courier New", 10))
        main_layout.addWidget(self.report_display)
        
        # أزرار التصدير
        export_layout = QHBoxLayout()
        
        self.export_txt_btn = QPushButton("📄 Export as TXT")
        self.export_txt_btn.clicked.connect(lambda: self.export_report('txt'))
        export_layout.addWidget(self.export_txt_btn)
        
        self.export_html_btn = QPushButton("🌐 Export as HTML")
        self.export_html_btn.clicked.connect(lambda: self.export_report('html'))
        export_layout.addWidget(self.export_html_btn)
        
        export_layout.addStretch()
        main_layout.addLayout(export_layout)
        
        self.setLayout(main_layout)
        
        # رسالة ترحيبية
        self.report_display.setPlainText("Select a report type to generate...")
    
    def generate_customers_report(self):
        customers = self.session.query(Customer).all()
        
        report = "=" * 60 + "\n"
        report += "CUSTOMERS REPORT\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += "=" * 60 + "\n\n"
        
        report += f"Total Customers: {len(customers)}\n\n"
        
        # حسب الحالة
        status_counts = {}
        for c in customers:
            status_counts[c.status] = status_counts.get(c.status, 0) + 1
        
        report += "By Status:\n"
        for status, count in status_counts.items():
            report += f"  • {status.capitalize()}: {count}\n"
        
        report += "\n" + "-" * 60 + "\n"
        report += "Customer List:\n"
        report += "-" * 60 + "\n\n"
        
        for c in customers[:50]:  # أول 50 فقط
            report += f"• {c.name}\n"
            report += f"  Email: {c.email or 'N/A'}\n"
            report += f"  Phone: {c.phone or 'N/A'}\n"
            report += f"  Status: {c.status}\n\n"
        
        self.report_display.setPlainText(report)
    
    def generate_deals_report(self):
        deals = self.session.query(Deal).all()
        
        report = "=" * 60 + "\n"
        report += "DEALS REPORT\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += "=" * 60 + "\n\n"
        
        total_value = sum([d.value or 0 for d in deals])
        report += f"Total Deals: {len(deals)}\n"
        report += f"Total Value: ${total_value:,.2f}\n\n"
        
        # حسب المرحلة
        stage_counts = {}
        stage_values = {}
        for d in deals:
            stage_counts[d.stage] = stage_counts.get(d.stage, 0) + 1
            stage_values[d.stage] = stage_values.get(d.stage, 0) + (d.value or 0)
        
        report += "By Stage:\n"
        for stage in ['prospecting', 'qualification', 'proposal', 'negotiation', 'won', 'lost']:
            count = stage_counts.get(stage, 0)
            value = stage_values.get(stage, 0)
            report += f"  • {stage.replace('_', ' ').title()}: {count} deals (${value:,.2f})\n"
        
        report += "\n" + "-" * 60 + "\n"
        report += "Top Deals:\n"
        report += "-" * 60 + "\n\n"
        
        sorted_deals = sorted(deals, key=lambda x: x.value or 0, reverse=True)[:10]
        for d in sorted_deals:
            report += f"• {d.title} - ${d.value:,.2f} ({d.stage})\n"
        
        self.report_display.setPlainText(report)
    
    def generate_tasks_report(self):
        tasks = self.session.query(Task).all()
        
        report = "=" * 60 + "\n"
        report += "TASKS REPORT\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += "=" * 60 + "\n\n"
        
        report += f"Total Tasks: {len(tasks)}\n\n"
        
        # حسب الحالة
        status_counts = {}
        for t in tasks:
            status_counts[t.status] = status_counts.get(t.status, 0) + 1
        
        report += "By Status:\n"
        for status, count in status_counts.items():
            report += f"  • {status.replace('_', ' ').title()}: {count}\n"
        
        report += "\n" + "-" * 60 + "\n"
        report += "Pending Tasks:\n"
        report += "-" * 60 + "\n\n"
        
        pending = [t for t in tasks if t.status != 'completed']
        for t in pending[:20]:
            report += f"• {t.title} (Due: {t.due_date or 'N/A'}) - {t.priority}\n"
        
        self.report_display.setPlainText(report)
    
    def export_report(self, format_type):
        content = self.report_display.toPlainText()
        
        if not content or content == "Select a report type to generate...":
            QMessageBox.warning(self, "Export", "Please generate a report first!")
            return
        
        if format_type == 'txt':
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Report", f"report_{datetime.now().strftime('%Y%m%d')}.txt",
                "Text Files (*.txt)"
            )
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "Success", f"Report saved to:\n{path}")
        
        elif format_type == 'html':
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Report", f"report_{datetime.now().strftime('%Y%m%d')}.html",
                "HTML Files (*.html)"
            )
            if path:
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CRM Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        pre {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
<pre>{content}</pre>
</body>
</html>"""
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                QMessageBox.information(self, "Success", f"Report saved to:\n{path}")