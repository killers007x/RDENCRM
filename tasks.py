from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QTextEdit, QDateEdit
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush
from database import Session
from models import Task, Customer

class TaskDialog(QDialog):
    def __init__(self, parent=None, obj=None, session=None):
        super().__init__(parent); self.obj=obj; self.session=session
        self.setWindowTitle("Add Task" if not obj else "Edit Task"); self.setMinimumWidth(400)
        lay=QFormLayout()
        self.title=QLineEdit(); self.desc=QTextEdit(); self.desc.setMaximumHeight(50)
        self.cust=QComboBox(); self.cust.addItem("None", None); [self.cust.addItem(c.name, c.id) for c in session.query(Customer).all()]
        self.date=QDateEdit(); self.date.setCalendarPopup(True); self.date.setDate(QDate.currentDate().addDays(7))
        self.prior=QComboBox(); self.prior.addItems(["low","medium","high"])
        self.stat=QComboBox(); self.stat.addItems(["pending","in_progress","completed"])
        for lbl,w in [("Title*:",self.title),("Desc:",self.desc),("Customer:",self.cust),("Due:",self.date),("Priority:",self.prior),("Status:",self.stat)]: lay.addRow(lbl,w)
        btns=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addRow(btns)
        self.setLayout(lay)
        if obj:
            self.title.setText(obj.title); self.desc.setText(obj.description or ""); self.prior.setCurrentText(obj.priority); self.stat.setCurrentText(obj.status)
            if obj.due_date: self.date.setDate(QDate.fromString(str(obj.due_date),"yyyy-MM-dd"))
            for i in range(self.cust.count()):
                if self.cust.itemData(i)==obj.customer_id: self.cust.setCurrentIndex(i); break
    def get_data(self):
        return {'title':self.title.text().strip(),'description':self.desc.toPlainText().strip(),'customer_id':self.cust.currentData(),'due_date':self.date.date().toPyDate(),'priority':self.prior.currentText(),'status':self.stat.currentText()}

class TasksTab(QWidget):
    def __init__(self):
        super().__init__(); self.session=Session(); self.init_ui(); self.load_data()
    def init_ui(self):
        top=QHBoxLayout()
        self.search=QLineEdit(); self.search.setPlaceholderText("Search tasks..."); self.search.textChanged.connect(self.filter)
        self.f_stat=QComboBox(); self.f_stat.addItems(["All","pending","in_progress","completed"]); self.f_stat.currentIndexChanged.connect(self.filter)
        self.f_prior=QComboBox(); self.f_prior.addItems(["All","low","medium","high"]); self.f_prior.currentIndexChanged.connect(self.filter)
        top.addWidget(self.search); top.addWidget(self.f_stat); top.addWidget(self.f_prior)
        self.btn_add=QPushButton("Add"); self.btn_add.clicked.connect(self.add)
        self.btn_edit=QPushButton("Edit"); self.btn_edit.clicked.connect(self.edit)
        self.btn_del=QPushButton("Delete"); self.btn_del.clicked.connect(self.delete)
        for b in [self.btn_add,self.btn_edit,self.btn_del]: top.addWidget(b)
        self.table=QTableWidget(); self.table.setColumnCount(6); self.table.setHorizontalHeaderLabels(["ID","Title","Customer","Due","Priority","Status"])
        self.table.setSortingEnabled(True); self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit); self.table.setColumnHidden(0, True)
        lay=QVBoxLayout(); lay.addLayout(top); lay.addWidget(self.table); self.setLayout(lay)
    def load_data(self):
        rows=self.session.query(Task).all(); self.table.setRowCount(len(rows))
        for i,t in enumerate(rows):
            for j,v in enumerate([t.id, t.title, t.customer.name if t.customer else "-", t.due_date.strftime("%Y-%m-%d") if t.due_date else "-", t.priority, t.status]):
                self.table.setItem(i,j,QTableWidgetItem(str(v)))
            c = {'high':'#ffe6e6','medium':'#fff3cd','low':'#d1ecf1'}.get(t.priority,'#ffffff')
            for col in range(6): self.table.item(i,col).setBackground(QBrush(QColor(c)))
    def filter(self):
        txt=self.search.text().lower(); st=self.f_stat.currentText(); pr=self.f_prior.currentText()
        for r in range(self.table.rowCount()):
            m = txt in self.table.item(r,1).text().lower()
            s = st=="All" or self.table.item(r,5).text()==st
            p = pr=="All" or self.table.item(r,4).text()==pr
            self.table.setRowHidden(r, not (m and s and p))
    def add(self):
        d=TaskDialog(self, session=self.session)
        if d.exec()==QDialog.DialogCode.Accepted:
            data=d.get_data()
            if not data['title']: return QMessageBox.warning(self,"Error","Title required")
            self.session.add(Task(**data)); self.session.commit(); self.load_data()
    def edit(self):
        r=self.table.currentRow()
        if r<0: return QMessageBox.warning(self,"Edit","Select a row")
        obj=self.session.get(Task, int(self.table.item(r,0).text()))
        d=TaskDialog(self, obj, self.session)
        if d.exec()==QDialog.DialogCode.Accepted:
            for k,v in d.get_data().items(): setattr(obj,k,v)
            self.session.commit(); self.load_data()
    def delete(self):
        r=self.table.currentRow()
        if r<0: return QMessageBox.warning(self,"Delete","Select a row")
        if QMessageBox.question(self,"Delete","Are you sure?")==QMessageBox.StandardButton.Yes:
            self.session.delete(self.session.get(Task, int(self.table.item(r,0).text()))); self.session.commit(); self.load_data()