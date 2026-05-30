from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import Session
from models import Customer, Deal, Task
from datetime import datetime, timedelta


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.init_ui()
        self.load_stats()

    def init_ui(self):
        lay = QVBoxLayout()

        # العنوان الرئيسي
        title = QLabel("Dashboard Overview")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        # البطاقات الإحصائية
        grid = QGridLayout()
        self.cards = {}

        # ألوان رمادية متناسقة مع الخلفية
        card_configs = [
            ("Total Customers", "#546e7a"),    # أزرق رمادي داكن
            ("Active Deals", "#607d8b"),        # أزرق رمادي
            ("Pipeline Value", "#78909c"),      # أزرق رمادي متوسط
            ("Pending Tasks", "#455a64")
        ]

        for i, (lbl, clr) in enumerate(card_configs):
            g = QGroupBox()
            g.setStyleSheet(f"""
                QGroupBox {{
                    background-color: {clr};
                    color: white;
                    border-radius: 8px;
                    padding: 15px;
                    border: none;
                }}
            """)

            vl = QVBoxLayout()

            # عنوان البطاقة
            t = QLabel(lbl)
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t.setStyleSheet("font-size: 11pt; font-weight: normal;")
            vl.addWidget(t)

            # القيمة
            v = QLabel("0")
            v.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl.addWidget(v)

            g.setLayout(vl)
            g.val_lbl = v
            grid.addWidget(g, 0, i)
            self.cards[lbl] = g

        lay.addLayout(grid)

        # قسم المهام القادمة
        upcoming_group = QGroupBox("Upcoming Tasks (Next 7 Days)")
        upcoming_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                padding-top: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
        """)

        upcoming_layout = QVBoxLayout()
        self.upcoming_label = QLabel("Loading...")
        self.upcoming_label.setWordWrap(True)
        self.upcoming_label.setStyleSheet("font-weight: normal; color: #ffffff;")
        upcoming_layout.addWidget(self.upcoming_label)
        upcoming_group.setLayout(upcoming_layout)

        lay.addWidget(upcoming_group)
        lay.addStretch()
        self.setLayout(lay)

    def load_stats(self):
        # إحصائيات العملاء
        total_customers = self.session.query(Customer).count()
        self.cards["Total Customers"].val_lbl.setText(str(total_customers))

        # إحصائيات الصفقات النشطة
        active_deals = self.session.query(Deal).filter(
            Deal.stage.notin_(['won', 'lost'])
        ).count()
        self.cards["Active Deals"].val_lbl.setText(str(active_deals))

        # القيمة الإجمالية
        val = sum([d.value or 0 for d in self.session.query(Deal).filter(
            Deal.stage != 'lost'
        ).all()])
        self.cards["Pipeline Value"].val_lbl.setText(f"${val:,.0f}")

        # المهام المعلقة
        pending_tasks = self.session.query(Task).filter(
            Task.status != 'completed'
        ).count()
        self.cards["Pending Tasks"].val_lbl.setText(str(pending_tasks))

        # المهام القادمة
        next_week = datetime.utcnow().date() + timedelta(days=7)
        upcoming = self.session.query(Task).filter(
            Task.due_date <= next_week,
            Task.status != 'completed'
        ).limit(5).all()

        if upcoming:
            tasks_text = "\n".join([
                f"• {t.title} (Due: {t.due_date}) - {t.priority}"
                for t in upcoming
            ])
        else:
            tasks_text = "No upcoming tasks"

        self.upcoming_label.setText(tasks_text)