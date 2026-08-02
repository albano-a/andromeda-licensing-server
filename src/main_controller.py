from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QHeaderView
from PyQt5 import uic
import json
import datetime
from core.api import Api
from core import db
from gui.icons.license_generator_rc import *

LMW = "src/gui/qt5/AdmaLicenseMainWindow.ui"


class AndromedaLicenseWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        uic.loadUi(LMW, self)

        self.tblControl.setColumnCount(6)
        self.tblControl.setHorizontalHeaderLabels(
            ["Email", "Hardware", "Generated At", "License Expiration", "Days Left", "Status"]
        )
        self.tblControl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.btnDeleteRecord.clicked.connect(self.delete_record)
        self.btnGenerate.clicked.connect(self.generate_license)

        db.init_db()
        self.load_table()

    def get_inputs(self):
        self.eml = self.txtEmail.text()
        self.hw = self.txtHardware.text()
        self.months = self.txtDuration.text()

        return self.eml, self.hw, self.months

    def load_table(self):
        self.tblControl.setRowCount(0)

        rows = db.load_licenses()

        for row_data in rows:
            row_position = self.tblControl.rowCount()
            self.tblControl.insertRow(row_position)
            self.tblControl.setItem(row_position, 0, QTableWidgetItem(row_data[0]))  # Email
            self.tblControl.setItem(row_position, 1, QTableWidgetItem(row_data[1]))  # Hardware
            self.tblControl.setItem(row_position, 2, QTableWidgetItem(row_data[2]))  # Generated At
            self.tblControl.setItem(
                row_position, 3, QTableWidgetItem(row_data[3])
            )  # License Expiration
            # Calculate days left
            expires_date = datetime.datetime.strptime(row_data[3], "%Y-%m-%d").date()
            today = datetime.date.today()
            days_left = (expires_date - today).days
            days_text = str(days_left) if days_left >= 0 else "Expired"
            self.tblControl.setItem(row_position, 4, QTableWidgetItem(days_text))
            # Status
            status = row_data[4] if row_data[4] else ("Active" if days_left >= 0 else "Expired")
            self.tblControl.setItem(row_position, 5, QTableWidgetItem(status))

    def generate_license(self):
        eml, hw, months = self.get_inputs()

        try:
            months = float(months)
        except ValueError:
            self.lblSituation.setText("Duration must be a number")
            return

        api = Api()
        result = api.generate_license(eml, hw, months)

        if result["ok"]:
            lic_data = result["license"]
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save License File",
                f"license_{eml.replace('@', '_')}_{str(datetime.date.today())}.json",
                "JSON Files (*.json)",
            )
            if filename:
                with open(filename, "w") as f:
                    json.dump(lic_data, f, indent=2)
                self.lblSituation.setText(f"License saved: {filename}")
            else:
                self.lblSituation.setText("License generation cancelled")
            self.load_table()
        else:
            self.lblSituation.setText(result["error"])

    def delete_record(self):
        current_row = self.tblControl.currentRow()
        if current_row >= 0:
            user_item = self.tblControl.item(current_row, 0)
            hardware_item = self.tblControl.item(current_row, 1)
            if user_item and hardware_item:
                db.delete_license(user_item.text(), hardware_item.text())
                self.load_table()
