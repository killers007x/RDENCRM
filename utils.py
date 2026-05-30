import pandas as pd
from fpdf import FPDF
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime

def export_data(data, columns, fmt, parent=None):
    if not data:
        QMessageBox.warning(parent, "Export", "No data to export!")
        return
    df = pd.DataFrame(data, columns=columns)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    if fmt == 'pdf':
        path, _ = QFileDialog.getSaveFileName(parent, "Save PDF", f"export_{ts}.pdf", "PDF (*.pdf)")
        if path:
            try:
                pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 10)
                w = 190/len(columns)
                for c in columns: pdf.cell(w, 8, str(c), 1, 0, "C")
                pdf.ln()
                pdf.set_font("Arial", "", 8)
                for r in df.values:
                    for v in r: pdf.cell(w, 6, str(v)[:20], 1, 0, "C")
                    pdf.ln()
                pdf.output(path)
                QMessageBox.information(parent, "Success", f"Saved to:\n{path}")
            except Exception as e: QMessageBox.critical(parent, "Error", str(e))
    else:
        exts = {'xlsx':'Excel (*.xlsx)','xls':'Excel Legacy (*.xls)','xltx':'Template (*.xltx)','csv':'CSV (*.csv)'}
        path, _ = QFileDialog.getSaveFileName(parent, "Save", f"export_{ts}.{fmt}", exts[fmt])
        if path:
            try:
                if fmt=='csv': df.to_csv(path, index=False, encoding='utf-8-sig')
                elif fmt=='xls': df.to_excel(path, index=False, engine='xlwt')
                else: df.to_excel(path, index=False, engine='openpyxl')
                QMessageBox.information(parent, "Success", f"Saved to:\n{path}")
            except Exception as e: QMessageBox.critical(parent, "Error", str(e))

def import_data(parent=None):
    path, _ = QFileDialog.getOpenFileName(parent, "Import", "", "Supported (*.xlsx *.xls *.xltx *.csv)")
    if not path: return None
    try:
        return pd.read_csv(path, encoding='utf-8-sig') if path.endswith('.csv') else pd.read_excel(path)
    except Exception as e:
        QMessageBox.critical(parent, "Import Error", str(e))
        return None