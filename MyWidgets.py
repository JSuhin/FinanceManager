"""
Custom Calendar Widget for Finance Manager v3
"""
import colorsys
import datetime
import logging
import sqlite3
import sys
import time
import timeit

import matplotlib.colors

import settings

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QDialog, QTreeWidgetItem, QDialogButtonBox, QVBoxLayout,\
    QMenu, QSplashScreen, QDateEdit, QComboBox, QLineEdit, QTableWidgetItem, QCompleter, QFrame, QScrollArea,\
    QAbstractItemView, QFileDialog
from PyQt6.QtGui import QTextCharFormat, QColor, QPixmap, QRegularExpressionValidator, QStandardItem
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer, Qt, QDateTime, QEvent, QRegularExpression
from functions import *
from requests.exceptions import ConnectionError

import matplotlib.pyplot as plt
from matplotlib.dates import MONTHLY, DateFormatter, rrulewrapper, RRuleLocator, drange, DAILY
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from math import ceil


class MySplashScreen(QSplashScreen):
    """Custom Splash Screen"""

    def __init__(self, pixmap):
        """Constructor"""

        super(MySplashScreen, self).__init__()

        # Load User Interface
        loadUi("ui/splashscreen.ui", self)

        # Remove frame
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        # Set Progress Bar text
        self.progressBar.setFormat("Loading data...")
        self.progressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add image
        if pixmap:
            pixmap = QPixmap(pixmap)
            pixmap = pixmap.scaledToHeight(600)
            self.setFixedSize(pixmap.size())
            self.setPixmap(pixmap)

    def progress(self, value, msg=None):
        """Sets Progress Bar value"""
        self.progressBar.setValue(value)
        if msg:
            self.progressBar.setFormat(msg)
        else:
            self.progressBar.setFormat("Loading data...")
        time.sleep(0.1)


class MyCalendarWidget(QWidget):
    """Custom calendar Widget - add and manage tasks"""

    def __init__(self):
        """Constructor"""
        super(QWidget, self).__init__()

        # Load Interface from Qt Designer
        loadUi("ui/mycalendar.ui", self)

        self.calendarWidget.setGridVisible(True)

        self.calendarWidget.selectionChanged.connect(self.calendarDateChanged)

        self.add_btn.clicked.connect(self.add)
        self.remove_btn.clicked.connect(self.remove)
        self.today_btn.clicked.connect(self.today)

        self.calendarDateChanged()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_update)
        self.timer.start(1000)

    def calendarDateChanged(self):
        """Calendar date change action"""
        date_selected = self.calendarWidget.selectedDate().toPyDate()
        self.updateTaskList(date_selected)
        self.format_dates()

    def updateTaskList(self, date):
        """Update Task list with selected date"""
        self.taskTreeWidget.clear()

        db = sqlite3.connect("bin/taskList.db")
        cursor = db.cursor()
        query = f"SELECT task, task_desc, completed FROM tasks WHERE date = '{date}'"
        results = cursor.execute(query).fetchall()

        for result in results:
            result = list(result)
            item = QTreeWidgetItem(result)

            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if item.text(2) == "YES":
                item.setCheckState(0, Qt.CheckState.Checked)
            elif item.text(2) == "NO":
                item.setCheckState(0, Qt.CheckState.Unchecked)

            self.taskTreeWidget.addTopLevelItem(item)

        db.close()

    def remove(self):
        """Remove Task from database and list"""
        task = self.taskTreeWidget.selectedIndexes()
        query = f"DELETE FROM tasks WHERE task = '{task[0].data()}' AND task_desc = '{task[1].data()}'"

        date = self.calendarWidget.selectedDate().toPyDate()
        date_format = QTextCharFormat()
        self.calendarWidget.setDateTextFormat(QDate.fromString(str(date), "yyyy-M-d"), date_format)

        conn = sqlite3.connect("bin/taskList.db")
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()

        self.calendarDateChanged()

    def add(self):
        """Create new task"""
        new_task = QDialog(self)
        loadUi("ui/taskeditor.ui", new_task)

        def save_new_task():
            """Save new task to task database"""

            # Data to save
            task_name = new_task.task_name.text()
            task_desc = new_task.task_desc.text()
            start = new_task.start_date.date().toPyDate()
            stop = new_task.end_date.date().toPyDate()
            # id_numb = set_id("bin/taskList.db", "tasks")

            # Database
            query = f"INSERT INTO tasks (task, task_desc, completed, date, date2) " \
                    f"VALUES ('{task_name}', '{task_desc}', 'NO', '{start}', '{stop}')"
            save_data("bin/taskList.db", query)

            new_task.close()
            self.calendarDateChanged()

        new_task.start_date.setDate(QDate(QDate.currentDate()))
        new_task.end_date.setDate(QDate(QDate.currentDate()))
        new_task.save_btn.clicked.connect(save_new_task)
        new_task.exec()

    def today(self):
        """Sets calendar to today's date"""
        today_date = QDate().currentDate()
        self.calendarWidget.setSelectedDate(today_date)
        logging.info("Calendar sets to today's date")

    def format_dates(self):
        """Format task dates in calendar"""

        # Gets all tasks from database
        dates = get_data_from_database("bin/taskList.db", f"SELECT date, completed FROM tasks")

        if len(dates) == 0:
            return

        dates = set([date[0] for date in dates])

        task_format = QTextCharFormat()
        for date in dates:
            tasks = get_data_from_database("bin/taskList.db",
                                           f"SELECT completed FROM tasks WHERE date = '{date}'")
            if len(tasks) == 1:
                if tasks[0][0] == "YES":
                    task_format.setBackground(QColor(0, 150, 0, 50))  # Green
                else:
                    task_format.setBackground(QColor(200, 0, 0, 50))  # Red
            else:
                all_completed = [t[0] for t in tasks]
                if "NO" in all_completed:
                    task_format.setBackground(QColor(200, 0, 0, 50))  # Red
                else:
                    task_format.setBackground(QColor(0, 150, 0, 50))  # Green

            self.calendarWidget.setDateTextFormat(QDate.fromString(date, "yyyy-M-d"), task_format)

    def check_update(self):
        """Updates task status in task database"""

        for i in range(self.taskTreeWidget.topLevelItemCount()):
            item = self.taskTreeWidget.topLevelItem(i)
            state = None
            if item.checkState(0) == Qt.CheckState.Checked:
                state = "YES"
            elif item.checkState(0) == Qt.CheckState.Unchecked:
                state = "NO"
            if state:
                query = f"UPDATE tasks SET completed = '{state}' WHERE task = '{item.text(0)}'"
                save_data("bin/taskList.db", query)


class LcdDateTime(QWidget):
    """Custom LCD Date and Time display widget"""

    def __init__(self):
        """Constructor"""
        super().__init__()
        loadUi("ui/lcddatetime.ui", self)

        # Updates every 1 second
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateLCD)
        self.timer.start(1000)

    def updateLCD(self):
        """Updates current time"""

        # Dan u tjednu
        week = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota", "Nedjelja"]
        st_curent_day = week[QDate.currentDate().dayOfWeek() - 1]

        current_time = QDateTime.currentDateTime()
        st_current_time = current_time.toString('hh:mm')
        st_current_date = current_time.toString('dd.MM.yyyy.')

        self.lcd_day.setText(st_curent_day.upper())
        self.lcd_time.setText(st_current_time)
        self.lcd_date.setText(st_current_date)


class ConfirmDialog(QDialog):
    """Confirm dialog"""

    def __init__(self, title="Warning!", label=None, styletext=None, list_label=None):
        """Constructor"""
        super().__init__()

        # Create style
        if styletext:
            self.setStyleSheet(styletext)

        # Set Window title
        self.setWindowTitle(title)

        # Add buttons and actions
        btn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(btn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Create layout
        self.layout = QVBoxLayout()

        # Add text (label)
        if label:
            self.layout.addWidget(QLabel(label))
        elif list_label:
            desc = ["Šifra", "Opis šifre", "Opis", "Iznos", "Datum", "Napomena", "ID"]
            for i, j in enumerate(desc):
                self.layout.addWidget(QLabel(j + ": " + list_label[i]))

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class BillEditor(QWidget):
    """Income and outcome bills"""

    def __init__(self, database=None):
        """Constructor"""

        super(QWidget, self).__init__()
        loadUi("ui/billseditor.ui", self)

        self.database = database if database else "Not selected"

        # Combo change
        self.combo_table.activated.connect(self.combo_change)

        # Update table with current
        self.update_table(database_path=database, bill_type="All")

        # Create context menu
        self.tree_bill.installEventFilter(self)
        self.tree_bill.doubleClicked.connect(self.action_update)

        # Button Actions
        self.btn_create.clicked.connect(self.action_create)

        # Format table
        self.tree_bill.setColumnWidth(0, 30)
        self.tree_bill.setColumnWidth(1, 125)
        self.tree_bill.setColumnWidth(2, 125)
        self.tree_bill.setColumnWidth(3, 125)
        self.tree_bill.setColumnWidth(4, 250)
        self.tree_bill.setColumnWidth(5, 300)
        self.tree_bill.setColumnWidth(6, 125)
        self.tree_bill.setColumnWidth(7, 300)

    def update_table(self, database_path, bill_type="all"):
        """Update Bill tree table"""

        # Connect database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Create query
        query = f"SELECT * FROM bills WHERE date >= '{self.year.value()}-01-01' AND date <= '{self.year.value()}-12-31'"
        if bill_type in ["Ulazni", "Income", "Ulazni računi"]:
            query += " AND TYPE = 'Ulazni račun'"
        elif bill_type in ["Izlazni", "Outcome", "Izlazni računi"]:
            query += " AND TYPE = 'Izlazni račun'"

        # Execute query
        cursor.execute(query)

        # Fetch results
        bills = cursor.fetchall()

        # Clean tree widget
        self.tree_bill.clear()

        # Insert new data
        for row in bills:
            # Convert to list
            try:
                row = list(row)
                row[6] = f"{row[6]:,.2f}"
                QTreeWidgetItem(self.tree_bill, [str(i) for i in row])
            except Exception as err:
                logging.error(err)

        # Close database
        conn.close()

    def combo_change(self):
        """Change bill type"""
        if self.combo_table.currentText() == "Ulazni računi":
            bill_type = "Ulazni"
        elif self.combo_table.currentText() == "Izlazni računi":
            bill_type = "Izlazni"
        else:
            bill_type = "All"

        self.update_table(database_path=self.database, bill_type=bill_type)

    # Menu Actions
    def action_refresh(self):
        """Refresh view"""
        print("REFRESH")

    def action_update(self):
        """Opens Bill Edit dialog"""

        # Create dialog
        dlg = QDialog(self)
        loadUi("ui/billedit.ui", dlg)
        dlg.setWindowTitle("Izmjena podataka računa")

        # Fill Dialog with selected data from table
        dlg.id_text.setText(self.tree_bill.selectedIndexes()[0].data())
        dlg.bill_type.setCurrentText(self.tree_bill.selectedIndexes()[1].data())
        dlg.number.setText(self.tree_bill.selectedIndexes()[2].data())
        dlg.date.setDate(QDate.fromString(self.tree_bill.selectedIndexes()[3].data(), "yyyy-M-d"))
        dlg.issued.setText(self.tree_bill.selectedIndexes()[4].data())
        dlg.adress.setText(self.tree_bill.selectedIndexes()[5].data())
        dlg.amount.setText(self.tree_bill.selectedIndexes()[6].data())
        dlg.desc.setText(self.tree_bill.selectedIndexes()[7].data())

        # Validators
        dlg.number.setValidator(
            QRegularExpressionValidator(QRegularExpression("[2][0][0-9]{2}/[0-1][0-9]-[0-9]{1,4}"), dlg.number))

        dlg.amount.setValidator(
                QRegularExpressionValidator(QRegularExpression("\d{1,10}[.]\d\d"), dlg.amount))

        # Button Action
        def save_action():
            """Save new bill"""

            # Create query
            query = f"UPDATE bills SET " \
                    f"type = '{dlg.bill_type.currentText()}', " \
                    f"number = '{dlg.number.text()}', " \
                    f"date = '{dlg.date.date().toPyDate()}', " \
                    f"issued = '{dlg.issued.text()}', " \
                    f"adress = '{dlg.adress.text()}', " \
                    f"amount = '{dlg.amount.text()}', " \
                    f"desc = '{dlg.desc.text()}' WHERE id = '{dlg.id_text.text()}'"

            # Execute query
            save_data(self.database, query)

            # Close dialog
            dlg.close()

            # Update bill table
            self.update_table(self.database, bill_type=self.combo_table.currentText())

        # Connect button actions
        dlg.btn_save.clicked.connect(save_action)
        dlg.btn_close.clicked.connect(dlg.close)

        dlg.exec()

    def action_delete(self):
        """Delete bill from database"""

        # Get selected bill
        id_number = self.tree_bill.selectedIndexes()[0].data()

        # Create query
        query = f"DELETE FROM bills WHERE id = {id_number}"

        # Execute query
        save_data(self.database, query)

        # Update view
        self.update_table(self.database, bill_type=self.combo_table.currentText())

    def action_create(self):
        """Open new bill entry Dialog"""
        dlg = QDialog(self)
        loadUi("ui/billinput.ui", dlg)
        dlg.setWindowTitle("Izrada novih računa")

        # Table Layout
        dlg.table.setColumnWidth(0, 125)
        dlg.table.setColumnWidth(1, 125)
        dlg.table.setColumnWidth(2, 125)
        dlg.table.setColumnWidth(3, 200)
        dlg.table.setColumnWidth(4, 300)
        dlg.table.setColumnWidth(5, 125)
        dlg.table.setColumnWidth(6, 300)

        # Define button actions
        def add_row_action():  # Button +
            """Adds row to table - cells are prepared for input"""
            dlg.table.insertRow(dlg.table.rowCount())

            combobox = QComboBox()
            combobox.addItems(["Ulazni račun", "Izlazni račun"])

            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDate(QDate.currentDate())

            # Amount with LineEdit
            number = QLineEdit()
            number.setPlaceholderText("npr. 2023/09-5")
            number.setValidator(
                QRegularExpressionValidator(QRegularExpression("[2][0][0-9]{2}/[0-1][0-9]-[0-9]{1,4}"), number))

            amount_edit = QLineEdit()
            amount_edit.setValidator(QRegularExpressionValidator(QRegularExpression("\d{1,10}[.]\d\d"), amount_edit))

            dlg.table.setCellWidget(dlg.table.rowCount() - 1, 0, combobox)
            dlg.table.setCellWidget(dlg.table.rowCount() - 1, 1, number)
            dlg.table.setCellWidget(dlg.table.rowCount() - 1, 2, date_edit)
            dlg.table.setCellWidget(dlg.table.rowCount() - 1, 3, QLineEdit())
            dlg.table.setCellWidget(dlg.table.rowCount() - 1, 4, QLineEdit())
            dlg.table.setCellWidget(dlg.table.rowCount() - 1, 5, amount_edit)
            dlg.table.setCellWidget(dlg.table.rowCount() - 1, 6, QLineEdit())

        def save_action():
            """Save data to database"""
            for irow in range(dlg.table.rowCount()):
                bill_type = dlg.table.cellWidget(irow, 0).currentText()
                number = dlg.table.cellWidget(irow, 1).text()
                date = dlg.table.cellWidget(irow, 2).date().toPyDate()
                issued = dlg.table.cellWidget(irow, 3).text()
                adress = dlg.table.cellWidget(irow, 4).text()
                amount = dlg.table.cellWidget(irow, 5).text()
                desc = dlg.table.cellWidget(irow, 6).text()

                query = f"INSERT INTO bills(type, number, date, issued, adress, amount, desc) " \
                        f"VALUES ('{bill_type}', '{number}', '{date}', '{issued}', '{adress}', '{amount}', '{desc}')"
                try:
                    save_data(self.database, query)
                except Exception as err:
                    logging.error(f"Error while saving new bills to database: {err}")

                dlg.close()
            self.update_table(database_path=self.database, bill_type=self.combo_table.currentText())

        # Connect button actions
        dlg.btn_add_row.clicked.connect(add_row_action)
        dlg.btn_remove_row.clicked.connect(lambda: dlg.table.removeRow(dlg.table.currentRow()))
        dlg.btn_clear.clicked.connect(lambda: dlg.table.setRowCount(0))
        dlg.btn_save.clicked.connect(save_action)
        dlg.btn_close.clicked.connect(lambda: dlg.close())

        dlg.setModal(True)
        dlg.showMaximized()

    def eventFilter(self, source, event):
        """Add context menu only if tree list item is selected"""
        if event.type() == QEvent.Type.ContextMenu and self.tree_bill.selectedIndexes():

            # Create context menu
            menu = QMenu()
            action_update = menu.addAction("Izmijeni")
            action_delete = menu.addAction("Izbriši")
            # action_refresh = menu.addAction("Refresh")

            # Connect actions
            action_update.triggered.connect(self.action_update)
            action_delete.triggered.connect(self.action_delete)
            # action_refresh.triggered.connect(self.action_refresh)

            # Display context menu
            menu.exec(event.globalPos())

            return True

        return super().eventFilter(source, event)


class BackUpRetriveWindow(QDialog):
    """Window for retriving files from Dropbox"""

    def __init__(self, parent):
        """Constructor"""

        super(BackUpRetriveWindow, self).__init__(parent=parent)
        loadUi("ui/dataretrive.ui", self)

        # Button actions connection
        self.btn_db.clicked.connect(self.action_db)
        self.btn_log.clicked.connect(self.action_log)
        self.btn_set.clicked.connect(self.action_set)
        self.btn_task.clicked.connect(self.action_task)

        self.setModal(True)
        self.show()

    # Button Actions
    def action_db(self):
        """Download database file from Dropbox"""
        try:
            download_database("/database.sqlite", "backup/backup_database.db")
            popup_message("Database retrived from Dropbox").exec()
            logging.info("Database retrived from Dropbox")
        except ConnectionError:
            popup_message("Error occured while retriving database file from Dropbox. Check internet connection!").exec()
            logging.info("Error occured while retriving database file from Dropbox. Check internet connection!")

    def action_log(self):
        """Download log file from Dropbox"""
        try:
            download_database("/log.txt", "backup/backup_log.txt")
            popup_message("Log file retrived from Dropbox").exec()
            logging.info("Log file retrived from Dropbox")
        except ConnectionError:
            popup_message("Error occured while retriving log file from Dropbox. Check internet connection!").exec()
            logging.info("Error occured while retriving log file from Dropbox. Check internet connection!")

    def action_set(self):
        """Download settings file from Dropbox"""
        try:
            download_database("/settings.db", "backup/backup_settings.db")
            popup_message("Settings file retrived from Dropbox").exec()
            logging.info("Settings file retrived from Dropbox")
        except ConnectionError:
            popup_message("Error occured while retriving settings file from Dropbox. Check internet connection!").exec()
            logging.info("Error occured while retriving settings file from Dropbox. Check internet connection!")

    def action_task(self):
        """Download Taski list from Dropbox"""
        try:
            download_database("/taskList.db", "backup/backup_taskList.db")
            popup_message("Task list retrived from Dropbox").exec()
            logging.info("Task list retrived from Dropbox")
        except ConnectionError:
            popup_message("Error occured while retriving Task list from Dropbox. Check internet connection!").exec()
            logging.info("Error occured while retriving Task list file from Dropbox. Check internet connection!")


class TokenInputWidget(QDialog):

    def __init__(self, parent=None):
        super(TokenInputWidget, self).__init__()
        loadUi("ui/token.ui", self)

        # Setup link
        app_link = "https://www.dropbox.com/developers/apps/info/2cnixj5ux96n7ob"
        self.link.setText(f'<a href="{app_link}"><b>Token Link</b></a>')
        self.link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.link.setOpenExternalLinks(True)

        # Button action
        self.btn_submit.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        # Set style
        if parent:
            self.setStyleSheet(parent.styleSheet())


class LoginWidget(QDialog):
    """Login Window"""

    def __init__(self, parent=None):
        super(LoginWidget, self).__init__()
        loadUi("ui/login.ui", self)

        # Set parent
        self.setParent(parent)

        # Initiate user type - passed from parent
        self.user_type = "User"
        if self.parent().user_type:
            self.user_type = self.parent().user_type
            self.set_user_type_combo()

        if self.user_type == "User":
            self.password_text.hide()
            self.password.hide()
        self.lbl_incorrect.hide()

        self.user.activated.connect(self.show_password)
        self.btn_login.clicked.connect(self.login_action)
        self.btn_close.clicked.connect(lambda: self.close())

        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle("Change user type")

    def show_password(self):
        """Show password line edit if admin selected"""

        if self.user.currentText() == "Admin":
            self.password_text.show()
            self.password.show()
            self.lbl_incorrect.hide()
        else:
            self.password_text.hide()
            self.password.hide()
            self.lbl_incorrect.hide()

    def hide_password(self):
        """Show password line edit if user selected"""
        if self.user_type == "User":
            self.password_text.hide()
            self.password.hide()
            self.lbl_incorrect.hide()

    def set_user_type_combo(self):
        """Sets user type combo"""
        if self.user_type == "User":
            self.user.setCurrentText("Korisnik")
        elif self.user_type == "Admin":
            self.user.setCurrentText("Admin")

    def login_action(self):
        """Loging action"""
        if self.user.currentText() == "Admin" and self.password.text() == "sokol1885":
            self.user_type = "Admin"
            self.close()
            self.lbl_incorrect.hide()
            logging.info("Login - User type: Admin")
        elif self.user.currentText() == "Admin" and self.password.text() != "sokol1885":
            self.lbl_incorrect.show()
            logging.info("Incorrect password entered for Admin type user")
        elif self.user.currentText() == "Korisnik":
            self.user_type = "User"
            self.close()
            self.hide_password()
            logging.info("Login - User type: User")
        else:
            self.user_type = None


class StatisticsWidget(QWidget):
    """Table statistics"""

    def __init__(self, database):
        """Constructor"""

        # Load interface
        super(StatisticsWidget, self).__init__()
        loadUi("ui/statisticstable.ui", self)

        # Disable edit
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Set database
        self.database = database

        # Connect combo change action
        self.combo_table.activated.connect(self.combo_change)

        # Prepare data
        data_to_show, codes = self.calculate_data()

        # Create table - income/outcome
        self.set_table(data_to_show, codes)

        # Add data to table
        self.show_data_in_table(data_to_show)

        # Add yearly totals

    @property
    def table_type(self):
        """Returns table type: income OR outcome"""
        return "income" if self.combo_table.currentText() == "Prihodi" else "outcome"

    def get_years(self, database, table):
        """Get available years from database"""
        query = f"SELECT day FROM {table}"
        dates = [date[0] for date in get_data_from_database(database, query)]

        for idate, date in enumerate(dates):
            if len(date) == 10:
                dates[idate] = datetime.datetime.strptime(date, "%Y-%m-%d")
            elif len(date) == 19:
                dates[idate] = datetime.datetime.strptime(date, "%Y-%m-%d 00:00:00")

        years = [date.year for date in dates]

        return set(years)

    def calculate_data(self):
        """Calculates sums per code per year"""

        # Get available years - initiation
        data = {key: None for key in self.get_years(self.database, self.table_type)}

        # Get codes from settings database
        codes = self.code_and_desc()

        # Create data to show
        for year in data.keys():
            amount = {}
            for code in codes.keys():
                query = f"SELECT amount FROM {self.table_type} WHERE code = {code} " \
                        f"AND day >= '{year}-01-01 00:00:00' AND day <= '{year}-12-31 00:00:00'"

                amount[code] = sum(float(entry[0]) for entry in get_data_from_database(self.database, query))
            data[year] = amount

        return data, codes

    def set_table(self, data, codes):
        """Setup table - row/column number and name"""
        self.table.setColumnCount(len(data))
        header_column = [str(iyear) for iyear in data.keys()]
        self.table.setHorizontalHeaderLabels(header_column)

        # Name rows
        # header_rows = [str(i) for i in (data[list(data.keys())[0]]).keys()]
        header_rows = [str(codes[i]) for i in codes.keys()]
        header_rows.append("Ukupno")
        self.table.setRowCount(len(header_rows))
        self.table.setVerticalHeaderLabels(header_rows)

    def show_data_in_table(self, data):
        """Put data in table"""
        for iyear, year in enumerate(data.keys()):

            # Yearly total
            total = sum([float(amount) for amount in data[year].values()])

            # Remove Cash income/outcome
            total = total - (list(data[year].values()).pop())

            # Total per code per year
            for icode, code in enumerate(data[year].keys()):
                self.table.setItem(icode, iyear, QTableWidgetItem(f"{data[year][code]:,.2f}"))

            self.table.setItem(len(data[year].keys()), iyear, QTableWidgetItem(f"{total:,.2f}"))

    def combo_change(self):
        """Income/Outcome statistics combo change action"""
        data, codes = self.calculate_data()
        self.set_table(data, codes)
        self.show_data_in_table(data)

    def code_and_desc(self):
        """Connects codes with description"""
        codes = {}
        query = f"SELECT * FROM {self.table_type}"

        for code, desc in get_data_from_database("bin/settings.db", query):
            codes[code] = desc

        return codes


class GraphicsWidget(QWidget):
    """Graphical display of data"""

    def __init__(self, parent, database, start, stop):
        """Constructor"""

        super(GraphicsWidget, self).__init__(parent=parent)
        loadUi("ui/graphics.ui", self)

        self.database = database
        self.start = start
        self.stop = stop

        # Connect combo and button action
        self.combo_graphics.activated.connect(self.combo_action)
        self.btn_save_image.clicked.connect(self.export_image)

        # Show Graphics
        canvas = self.period_plot(self.database)

        while self.layout_plot.count() > 0:
            self.layout_plot.removeItem(self.layout_plot.itemAt(0))

        self.layout_plot.addWidget(canvas)

    def period_plot(self, database):
        """Draw income and outcome for chosen period - returns canvas widget"""

        # Colors
        background = self.parent().palette().base().color().name()
        text = self.parent().palette().text().color().name()

        # Chosen period
        date_from = self.start.date().toPyDate()
        date_to = self.stop.date().toPyDate()

        # Retrive data
        income_dates, income = calculate_totals(date_from, date_to, "income", database)
        outcome_dates, outcome = calculate_totals(date_from, date_to, "outcome", database)

        # set_ylim
        try:
            ylim = max([max(income), max(outcome)])
            ylim = ceil(ylim / 1000) * 1000
        except Exception as e:
            logging.info(e)
            logging.info("Setting ylim to 2000")
            ylim = 2000

        # Handle dates
        income_dates = handle_dates(income_dates)
        outcome_dates = handle_dates(outcome_dates)

        # Manage date ticks
        rule = rrulewrapper(MONTHLY, interval=1)
        loc = RRuleLocator(rule)
        formatter = DateFormatter("%b")

        # Create Figure
        fig = plt.figure(facecolor=background)

        # Plot income
        plt.subplot(2, 1, 1, facecolor=background)
        plt.subplots_adjust(hspace=.5)
        plt.plot_date(income_dates, income, "-", color=text)

        # Add label, grid and title
        plt.ylabel("\N{euro sign}", color=text)
        plt.grid(True, color=text)
        plt.title("PRIHODI", color=text)

        # Draw ticks on x axes
        ax = plt.gca()
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_tick_params(rotation=30, labelsize=10, colors=text)

        # Set y axis color
        ax.yaxis.set_tick_params(colors=text)
        ax.set_ylim([0, ylim])

        # Frame color
        ax.spines['top'].set_color(text)
        ax.spines['bottom'].set_color(text)
        ax.spines['left'].set_color(text)
        ax.spines['right'].set_color(text)

        # Plot outcome
        plt.subplot(2, 1, 2, facecolor=background)
        plt.plot_date(outcome_dates, outcome, "-", color=text)
        plt.ylabel("\N{euro sign}", color=text)
        plt.grid(True, color=text)
        plt.title("RASHODI", color=text)

        # Add label, grid and title
        ax = plt.gca()
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_tick_params(rotation=30, labelsize=10, colors=text)

        # Set y axis color
        ax.yaxis.set_tick_params(colors=text)
        ax.set_ylim([0, ylim])

        # Frame color
        ax.spines['top'].set_color(text)
        ax.spines['bottom'].set_color(text)
        ax.spines['left'].set_color(text)
        ax.spines['right'].set_color(text)

        return FigureCanvasQTAgg(fig)

    def draw_yearly_data(self, database):
        """Draw income, outcome and profit data by year - return canvas"""

        # Colors
        background = self.parent().palette().base().color().name()
        text = self.parent().palette().text().color().name()
        if QColor(text).getRgbF()[0] > 0.51:
            bar_color_1 = tuple([i-0.2 for i in QColor(text).getRgbF()[0:3]])
            bar_color_2 = tuple([i-0.3 for i in QColor(text).getRgbF()[0:3]])
            bar_color_3 = tuple([i-0.4 for i in QColor(text).getRgbF()[0:3]])
            grid = tuple([i + 0.05 for i in QColor(background).getRgbF()[0:3]])
        else:
            bar_color_1 = tuple([i - 0.2 + 0.5 for i in QColor(text).getRgbF()[0:3]])
            bar_color_2 = tuple([i - 0.3 + 0.5 for i in QColor(text).getRgbF()[0:3]])
            bar_color_3 = tuple([i - 0.4 + 0.5 for i in QColor(text).getRgbF()[0:3]])
            grid = tuple([i - 0.05 for i in QColor(background).getRgbF()[0:3]])

        if QColor(background).getRgbF() in [(1.0, 1.0, 1.0, 1.0), (0.6872549176216125,
                                                                   0.7500000119209289, 0.8127451062202453)]:
            grid = "grey"

        # Get years
        years = StatisticsWidget(database).get_years(database, "income")

        # Retrive data
        income_per_year = {}
        outcome_per_year = {}
        diff = {}
        for year in years:
            query = f"SELECT amount FROM income WHERE day >= '{year}-01-01' AND day <= '{year}-12-31'"
            income_per_year[year] = sum([i[0] for i in get_data_from_database(database, query)])
            query = f"SELECT amount FROM outcome WHERE day >= '{year}-01-01' AND day <= '{year}-12-31'"
            outcome_per_year[year] = sum([i[0] for i in get_data_from_database(database, query)])
            diff[year] = income_per_year[year]-outcome_per_year[year]

        # Set limits and labels
        ylim = max([max(income_per_year.values()), max(outcome_per_year.values())])
        ylim = ceil(ylim / 1000) * 1000 * 1.1

        # Bar with
        bar_width = 0.25

        # Create Figure
        fig = plt.figure(facecolor=background)

        # Create bar plot
        plt.subplot(facecolor=background)
        plt.bar([i - bar_width for i in income_per_year.keys()], income_per_year.values(), color=bar_color_1, width=bar_width)
        plt.bar(outcome_per_year.keys(), outcome_per_year.values(), color=bar_color_2, width=bar_width)
        plt.bar([i + bar_width for i in income_per_year.keys()], diff.values(), color=bar_color_3, width=bar_width)

        plt.ylabel("\N{euro sign}", color=text)
        plt.grid(True, linestyle='--', color=grid)
        plt.title("PRIHODI I RASHODI", color=text)

        # Set x axis
        ax = plt.gca()
        ax.xaxis.set_tick_params(colors=text)
        ax.set_xlim([2020, 2025])

        # Set y axis color
        ax.yaxis.set_tick_params(colors=text)
        ax.set_yticklabels(["{:,.0f}".format(label) for label in ax.get_yticks()])
        ax.set_ylim([0, ylim])

        # Frame color
        ax.spines['top'].set_color(text)
        ax.spines['bottom'].set_color(text)
        ax.spines['left'].set_color(text)
        ax.spines['right'].set_color(text)

        return FigureCanvasQTAgg(fig)

    def combo_action(self):
        """Change shown graphics"""
        if self.combo_graphics.currentText() == "Pregled perioda":
            canvas = self.period_plot(self.database)
        else:
            canvas = self.draw_yearly_data(self.database)

        while self.layout_plot.count() > 0:
            self.layout_plot.removeItem(self.layout_plot.itemAt(0))

        self.layout_plot.addWidget(canvas)

    def export_image(self):
        """Save image to png"""

        # Get current image
        canvas = self.layout_plot.itemAt(0).widget()

        # Ask for file
        filepath = QFileDialog(self, "Choose path for image", ".", "PNG (*.png)")
        filepath.setFileMode(QFileDialog.FileMode.AnyFile)
        filepath.exec()

        if filepath.result() == 0:
            logging.info("QDialog cancel button pressed")
            return
        else:
            path = filepath.selectedFiles()[0]
            logging.info("Selected PNG file for writing data")

        # Save image
        canvas.print_png(path)
        logging.info(f"Image saved to file: {path}")


class QHLine(QFrame):
    """Horizontal line"""
    def __init__(self):
        """Constructor"""
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class LinksWidget(QWidget):
    """Widget containing links"""

    def __init__(self, style="Default"):
        """Constructor"""
        super(LinksWidget, self).__init__()

        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Links list
        links = {
            "Gmail": "https://mail.google.com/",
            "Karlovačka banka": "http://kaba.hr/",
            "Som-sport": "https://som-sport.com/",
            "IT Sport": "https://itsport.hr/app/login",
            "GK Sokol Karlovac": "gksokolkarlovac.hr",
            "Hrvatski gimnastički savez": "http://hgs.hr",
            "Registar udruga": "https://registri.uprava.hr/#!udruge",
            "Registar neprofitnih organizacija": "https://banovac.mfin.hr/rnoprt/",
            "Ministarstvo turizma i sporta": "https://mint.gov.hr/",
        }

        # Get link style
        link_style = create_link_style(style)

        # Add links to dashboard
        for ikey, key in enumerate(links.keys()):
            link = QLabel(f'<a {link_style} href="{links[key]}"><b>{key}</b></a>')
            link.setAlignment(Qt.AlignmentFlag.AlignCenter)
            link.setOpenExternalLinks(True)
            link.setToolTip(links[key])

            layout.addWidget(link)
            if ikey < len(links.keys()) - 1:
                layout.addWidget(QHLine())


class IzvodControlWidget(QWidget):
    """Under Construction"""

    def __init__(self, database: str=None):
        """Constructor"""

        # Load interface
        super(IzvodControlWidget, self).__init__()
        loadUi("ui/izvodcontrol.ui", self)

        # Connect button action
        self.btn_run_control.clicked.connect(self.run_control_action)

        # Set defaults
        if database:
            print("Set year combobox")

            print("Set max report number")

        self.show()

    def run_control_action(self):
        """Runs report control"""

        print("Run report number control")


def kn_to_euro(database):
    """Convert currency from HKN to EURO"""
    # Open database
    conn = sqlite3.connect(database)

    # Create cursor
    cursor = conn.cursor()

    for table in ["income", "outcome"]:

        # Execute query
        cursor.execute(f"SELECT * FROM {table} WHERE day <= '2022-12-31'")

        result = cursor.fetchall()

        for i in result:
            query = f"UPDATE {table} SET amount = {i[3]/7.5345:.2f} WHERE id = {i[6]}"
            cursor.execute(query)

    conn.commit()


if __name__ == '__main__':
    #timeit.timeit()
    #kn_to_euro("bin/GKSokol_2023.sqlite")
    app = QApplication(sys.argv)

    # token_dlg = TokenInputWidget()
    # if token_dlg.exec():
    #     token = token_dlg.token_str
    # print(token)

    #widget = LinksWidget()
    widget = IzvodControlWidget(database="bin/GKSokol_2024.sqlite")
    # widget = StatisticsWidget(database="bin/GKSokol.sqlite")
    # widget = BillEditor(database="bin/GKSokol.sqlite")
    # widget = BackUpRetriveWindow(None)
    # widget = MyCalendarWidget()
    # widget = LoginWidget()
    # widget = GraphicsWidget(parent=None, database="bin/GKSokol.sqlite", start=QDate(2023, 1, 1), stop=QDate(2023, 1, 31))
    sys.exit(app.exec())

