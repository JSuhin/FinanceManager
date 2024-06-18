"""Graphical interface for Finance Manager v3.0"""
import datetime
# pylint: disable=line-too-long

import logging
import os.path
import sys
import time
import matplotlib.pyplot
import requests.exceptions
import pyqtgraph as pg
import qtawesome as qta
import functions as fn

from PyQt6.QtWidgets import QFileDialog, QComboBox, QLineEdit, QTableWidgetItem, QDateEdit, QDateTimeEdit, QStyle,\
    QScrollArea
from PyQt6 import uic
from PyQt6.QtGui import QRegularExpressionValidator, QDesktopServices, QTextFormat
from PyQt6.QtCore import QUrl, QRegularExpression, Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.dates import MONTHLY, DateFormatter, rrulewrapper, RRuleLocator, drange, DAILY

from settings import Settings
from MyWidgets import *


class UI(QWidget):
    """Main class for User Interface"""

    def __init__(self):
        super().__init__()

        # Login - User type
        self.user_type = "User"
        self.menu_hidden = False

        # Initiation - check for necessary files and folders
        #self.initiation_check(settings_path="bin/settings.db")
        #print("System exit in UserInterface.py - line 41 (for debugging)"); sys.exit()

        # Display SplashScreen
        splash = MySplashScreen(pixmap="images/splashscreen.png")
        splash.show()
        splash.progress(10, msg="Preparing users information")

        # Load GUI
        uic.loadUi("ui/manager.ui", self)
        logging.info("User Interface loaded")
        splash.progress(20, "Loading interface")

        # Load settings from file
        global settings
        settings = Settings(file="bin/settings.db")

        # Set style
        self.setStyleSheet(fn.create_stylesheet(style=settings.get_setting("style")))
        splash.progress(30, msg="Setting stylesheet")

        # Window options
        self.setWindowTitle(f'Finance Manager v3.0 - {settings.get_setting("club")} - {self.user_type}')
        # self.SetWindowIcon(settings.get_setting("icon"))

        # Add Calendar to Dashboard
        calendar = MyCalendarWidget()
        self.calendar_frame.addWidget(calendar)
        calendar.format_dates()
        splash.progress(40, msg="Starting Dashboard - Calendar Widget")

        # Setup LCD Clock
        datetime_widget = LcdDateTime()
        self.dashboard_1.addWidget(datetime_widget)
        splash.progress(50, msg="Starting Dashboard - Date Widget")

        # Setup BillEditor
        self.bill_editor = BillEditor(database=settings.get_setting("database"))
        self.bill_frame.addWidget(self.bill_editor)
        splash.progress(60, msg="Loading Bill editor")

        self.statistics_widget = StatisticsWidget(database=settings.get_setting("database"))
        self.statistics_frame.addWidget(self.statistics_widget)
        splash.progress(65, msg="Loading Statistics Widget")

        # Set object properties - Dates
        date_from = self.__getattribute__("date_from")
        date_from.setDate(QDate(QDate.currentDate().year(), 1, 1))

        date_to = self.__getattribute__("date_to")
        date_to.setDate(QDate(QDate.currentDate().year(), 12, 31))

        # Set object properties - Combo box
        self.combo_income.addItem("0")
        self.combo_income.addItems(settings.get_income_codes())
        self.combo_income.activated.connect(self.code_select_income)

        self.income_desc.setText("SVI PRIHODI")

        self.combo_outcome.addItem("0")
        self.combo_outcome.addItems(settings.get_outcome_codes())
        self.combo_outcome.activated.connect(self.code_select_outcome)

        self.outcome_desc.setText("SVI RASHODI")

        # Add icons to buttons
        self.btn_hide.setIcon(qta.icon("fa5s.minus"))
        self.btn_network.setIcon(qta.icon("fa5s.wifi"))
        self.btn_exit.setIcon(qta.icon("fa5s.window-close"))
        self.btn_backup.setIcon(qta.icon("fa5s.file-export"))

        # Set tooltip
        self.btn_exit.setToolTip("Zatvori aplikaciju")
        self.btn_backup.setToolTip("Spremi datoteke na Dropbox")

        # Check internet connection for the first time
        self.click_btn_network()

        # Add functionality
        self.btn_show.clicked.connect(self.click_btn_show)
        self.btn_excel_2.clicked.connect(self.click_excel_btn)
        self.btn_exit.clicked.connect(self.close)
        self.btn_backup.clicked.connect(self.click_btn_backup)
        self.btn_hide.clicked.connect(self.click_btn_hide)
        self.btn_network.clicked.connect(self.click_btn_network)

        self.income_btn1.clicked.connect(self.click_income_btn1)
        self.income_btn2.clicked.connect(self.click_income_btn2)
        self.income_btn3.clicked.connect(self.click_income_btn3)

        self.outcome_btn1.clicked.connect(self.click_outcome_btn1)
        self.outcome_btn2.clicked.connect(self.click_outcome_btn2)
        self.outcome_btn3.clicked.connect(self.click_outcome_btn3)

        splash.progress(70, msg="Setting up databases, icons and buttons")

        # Design - INCOME TREE
        fn.set_tree_layout(self.tree_income)
        self.tree_income.doubleClicked.connect(self.click_income_btn2)

        # Design - OUTCOME TREE
        fn.set_tree_layout(self.tree_outcome)
        self.tree_outcome.doubleClicked.connect(self.click_outcome_btn2)

        splash.progress(75, msg="Loading Income, Outcome and Report Widgets")

        # Design - REPORT TREES (income/outcome)
        fn.set_report_tree_layout(self.report_income)
        fn.set_report_tree_layout(self.report_outcome)

        # Add data
        self.click_btn_show()

        # Income and outcome input table
        fn.set_table_layout(self.io_table)

        self.browse_btn.clicked.connect(self.click_browse_btn)
        self.add_row.clicked.connect(self.click_add_row)
        self.remove_row.clicked.connect(self.click_remove_row)
        self.save_btn.clicked.connect(self.click_save_btn)
        self.clear_btn.clicked.connect(self.click_clear_btn)

        # Links ######################################################################################################
        self.links_widget = LinksWidget(style=settings.get_setting("style"))
        self.links_scroll.setWidget(self.links_widget)

        splash.progress(80, msg="Creating links on Dashboard")

        # FEATURES ###################################################################################################
        self.tabWidget.setTabVisible(1, bool(int(settings.get_setting("table"))))  # Table
        self.tabWidget.setTabVisible(2, bool(int(settings.get_setting("income"))))  # Income
        self.tabWidget.setTabVisible(3, bool(int(settings.get_setting("outcome"))))  # Outcome
        self.tabWidget.setTabVisible(4, bool(int(settings.get_setting("report"))))  # Report
        self.tabWidget.setTabVisible(5, bool(int(settings.get_setting("bills"))))  # Bills
        self.tabWidget.setTabVisible(6, bool(int(settings.get_setting("statistics"))))  # Statistics
        self.tabWidget.setTabVisible(7, bool(int(settings.get_setting("graphics"))))  # Graphics

        self.tabWidget.setTabEnabled(1, bool(int(settings.get_setting("table"))))  # Table
        self.tabWidget.setTabEnabled(2, bool(int(settings.get_setting("income"))))  # Income
        self.tabWidget.setTabEnabled(3, bool(int(settings.get_setting("outcome"))))  # Outcome
        self.tabWidget.setTabEnabled(4, bool(int(settings.get_setting("report"))))  # Report
        self.tabWidget.setTabEnabled(5, bool(int(settings.get_setting("bills"))))  # Bills
        self.tabWidget.setTabEnabled(6, bool(int(settings.get_setting("statistics"))))  # Statistics
        self.tabWidget.setTabEnabled(7, bool(int(settings.get_setting("graphics"))))  # Graphics

        # Show Dashboard when app starts
        self.tabWidget.setCurrentIndex(0)

        splash.progress(90, msg="Handling licencing")

        self.setFocus()
        self.showMaximized()

        splash.progress(100, msg="Starting Finance Manager III")

    def initiation_check(self, settings_path=None):
        """Find/Ask for file paths"""

        # Get file path from Settings file (if settings file present)
        database_path = None
        log_path = None

        # Settings file
        if settings_path:  # IF settings file given
            logging.info(f"Settings file given: {settings_path}")

            if os.path.isfile(settings_path):  # IF file exists
                logging.info("File exists")

                # Check for settings table
                # query = "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"

                if table_exists(settings_path, "settings"):  # IF table exists
                    logging.info("Settings table found")
                    database_path = get_data_from_database(
                        settings_path, "SELECT value FROM settings WHERE setting='database'")[0][0]
                    log_path = get_data_from_database(
                        settings_path, "SELECT value FROM settings WHERE setting='log_filename'")[0][0]
                    logging.info(f"Database path: {database_path}")
                    logging.info(f"Log path: {log_path}")
                else:
                    logging.error(f"Settings table not in given settings file: {settings_path}")
            else:
                logging.error("Settings file does't exists!")
        else:
            logging.error("Settings file not given")

        # DATABASE CHECK
        # Check for income table
        if table_exists(database_path, "income"):
            logging.info("Income table found in database file")
        else:
            logging.info("No income table in database file")
            fn.popup_message("No income table in given database").exec()
            sys.exit()

        # Check for outcome table
        if table_exists(database_path, "outcome"):
            logging.info("Outcome table found in database file")
        else:
            logging.info("No outcome table in database file")
            fn.popup_message("No outcome table in given database").exec()
            sys.exit()

        # Splash Screen Image
        if os.path.isfile("images/splashscreen.png"):
            logging.info("SplashScreen image found")
        else:
            logging.warning("SplashScreen image not found")
            fn.popup_message("SplashScreen image not found").exec()
            sys.exit()

        # Task list file

    def reboot(self):
        """Reboot app"""
        logging.info("Reboot Finance Manager")
        try:
            self.close()
            self.__init__()
        except Exception as err:
            logging.error(f"Reboot failed: {err}")

    def click_btn_backup(self):
        """Create backup files on Dropbox"""
        fn.popup_message("Spremanje podataka na Dropbox.", style=self.styleSheet()).exec()

        try:
            # Input toke from web
            token_dlg = TokenInputWidget(parent=self)

            if token_dlg.exec():
                token = token_dlg.token.text()

            fn.backup_file(settings.get_setting("database"), "/database.sqlite", token)
            fn.backup_file(settings.get_setting("log_filename"), "/log.txt", token)
            fn.backup_file("bin/settings.db", "/settings.db", token)
            fn.backup_file("bin/taskList.db", "/taskList.db", token)
            fn.popup_message("Podaci uspješno spremljeni na Dropbox.", style=self.styleSheet()).exec()
            logging.info("File backup complete!")
        except requests.exceptions.ConnectionError:
            fn.popup_message("Neuspješno spremanje podataka! Provjeriti pristup internetu!",
                             style=self.styleSheet()).exec()
            logging.info("No internet connection!")
        except Exception as error:
            logging.error(error)

    def click_btn_show(self):
        """Show all data considering choosen dates and codes"""

        # Set Dashboard
        year = QDateTime.currentDateTime().toPyDateTime().year

        # Total income
        income, outcome = fn.calculate_year_totals(year, settings.get_setting("database"))
        daily_income, daily_outcome = fn.calculate_daily_totals(settings.get_setting("database"))

        self.dashboard_income.setText(f"{income:,.2f} \N{euro sign}")
        self.dashboard_outcome.setText(f"{outcome:,.2f} \N{euro sign}")
        self.dashboard_total.setText(f"{income - outcome:,.2f} \N{euro sign}")

        self.dashboard_income_2.setText(f"{daily_income:,.2f} \N{euro sign}")
        self.dashboard_outcome_2.setText(f"{daily_outcome:,.2f} \N{euro sign}")
        self.dashboard_total_2.setText(f"{daily_income - daily_outcome:,.2f} \N{euro sign}")

        # Chosen period
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        # Chosen codes
        code_income = self.combo_income.currentText()
        code_outcome = self.combo_outcome.currentText()

        # Get income/oucome data from database
        income_data = fn.get_data_from_database(settings.get_setting("database"),
                                                self.create_query("income", date_from, date_to, str(code_income)))
        outcome_data = fn.get_data_from_database(settings.get_setting("database"),
                                                 self.create_query("outcome", date_from, date_to, str(code_outcome)))

        # Put data to list
        self.update_tree_list(self.tree_income, income_data)
        self.update_tree_list(self.tree_outcome, outcome_data)

        # Get income/outcome totals for report display
        report_data_income, report_data_outcome = self.create_report_data(date_from, date_to)
        self.update_tree_list(self.report_income, report_data_income)
        self.update_tree_list(self.report_outcome, report_data_outcome)

        income_sum = self.calculate_total(income_data)
        outcome_sum = self.calculate_total(outcome_data)
        report_income_total = self.calculate_total(report_data_income)
        report_outcome_total = self.calculate_total(report_data_outcome)

        self.income_total.setText(f"UKUPNO: {income_sum:,.2f} \N{euro sign}")
        self.outcome_total.setText(f"UKUPNO: {outcome_sum:,.2f} \N{euro sign}")
        self.total_income.setText(f"UKUPNO PRIHODI: {report_income_total:,.2f} \N{euro sign}")
        self.total_outcome.setText(f"UKUPNO RASHODI: {report_outcome_total:,.2f} \N{euro sign}")
        self.total.setText(f"UKUPNO: {(report_income_total - report_outcome_total):,.2f} \N{euro sign}")

        # Add plots to App
        while self.plot.count() > 0:
            self.plot.removeItem(self.plot.itemAt(0))
        self.plot.addWidget(GraphicsWidget(self, settings.get_setting("database"), self.date_from, self.date_to))

    def click_btn_hide(self):
        """Hide and show menu"""
        if self.menu_hidden:
            self.frame_menu.show()
            self.menu_hidden = False
            self.btn_hide.setIcon(qta.icon("fa5s.minus"))
        else:
            self.frame_menu.hide()
            self.menu_hidden = True
            self.btn_hide.setIcon(qta.icon("fa5s.plus"))

    def click_btn_network(self):
        """Check for internet access"""
        try:
            urllib.request.urlopen(url="http://google.com")
            self.btn_network.setIcon(qta.icon("fa5s.wifi", color="green"))
            self.btn_network.setToolTip("Pristup internetu omogućen")
            logging.info("Internet Access")
        except urllib.error.URLError:
            self.btn_network.setIcon(qta.icon("fa5s.wifi", color="red"))
            self.btn_network.setToolTip("Nema pristupa internetu")
            logging.info("No Internet Access")

    '''
    def plot_graphs(self):
        """Create plots"""

        # Chosen period
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        # Retrive data
        dates, income = fn.plot_data(date_from, date_to, "income", settings.get_setting("database"))

        # Plot Income data
        graph_income = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
        graph_income.showGrid(True, True)
        graph_income.plotItem.plot(income)
        graph_income.plot(x=range(len(dates)), y=income, pen="black", )
        graph_income.setBackground((235, 235, 235))

        styles = {"color": "k", "font-size": "14px"}
        graph_income.setLabel("left", "PRIHODI [\N{euro sign}]", **styles)

        graph_income.getAxis('left').setTextPen('black')
        graph_income.getAxis('left').setPen('black')

        graph_income.getAxis('bottom').setTextPen('black')
        graph_income.getAxis('bottom').setPen('black')

        # Place to put graphs/plots
        self.plot.addWidget(graph_income)

    def plot_income(self):
        """Plot income - under construction"""

        # Chosen period
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        # Retrive data
        dates, income = fn.calculate_totals(date_from, date_to, "income", settings.get_setting("database"))

        # Handle dates
        dates = fn.handle_dates(dates)

        # Manage date ticks
        rule = rrulewrapper(MONTHLY, interval=1)
        loc = RRuleLocator(rule)
        formatter = DateFormatter("%b")

        # Create image
        #fig, ax = matplotlib.pyplot.subplots(1, 1)
        #ax.plot_date(dates, income, '-')

        #ax.xaxis.set_major_locator(loc)
        #ax.xaxis.set_major_formatter(formatter)
        #ax.xaxis.set_tick_params(rotation=30, labelsize=10)

        #fig.xlabel("Datum")
        #fig.ylabel("Euro")

        #fig.set_facecolor("blue")
        #ax.set_facecolor("blue")

        canvas = FigureCanvasQTAgg(fig)

        while self.plot.count() > 0:
            self.plot.removeItem(self.plot.itemAt(0))

        # Add income graph to widget
        self.plot.addWidget(canvas)

    '''
    def click_excel_btn(self):
        """Export income table to excel file"""
        logging.info("Export to Excel button clicked")

        # Get data from tree widgets
        logging.debug("Getting income data")
        income_data = [[self.tree_income.topLevelItem(irow).text(i)
                        for i in range(self.tree_income.columnCount())]
                       for irow in range(self.tree_income.topLevelItemCount())]

        logging.debug("Getting outcome data")
        outcome_data = [[self.tree_outcome.topLevelItem(irow).text(i)
                         for i in range(self.tree_outcome.columnCount())]
                        for irow in range(self.tree_outcome.topLevelItemCount())]

        logging.debug("Getting income report data")
        income_report_data = [[self.report_income.topLevelItem(irow).text(i)
                               for i in range(self.report_income.columnCount())]
                              for irow in range(self.report_income.topLevelItemCount())]

        logging.debug("Getting outcome report data")
        outcome_report_data = [[self.report_outcome.topLevelItem(irow).text(i)
                                for i in range(self.report_outcome.columnCount())]
                               for irow in range(self.report_outcome.topLevelItemCount())]

        # Ask for file
        path = QFileDialog(self, "Open file", ".", "Excel (*.xls, *.xlsx)")
        path.setFileMode(QFileDialog.FileMode.AnyFile)
        path.exec()
        if path.result() == 0:
            logging.info("QDialog cancel button pressed")
            return
        else:
            output_file = path.selectedFiles()[0]
            logging.info("Selected Excel file for writing data")

        # Export to excel - function for saving
        fn.write_to_excel(income_data, output_file, sheet="Prihodi")
        fn.write_to_excel(outcome_data, output_file, sheet="Rashodi")
        fn.write_to_excel(income_report_data, output_file, sheet="Suma prihodi")
        fn.write_to_excel(outcome_report_data, output_file, sheet="Suma rashodi")
        logging.info("Data writen to Excel file")

        fn.popup_message(text=f"Sva izvješća spremljena u excel tablicu:\n{output_file}").exec()

    def code_select_income(self):
        """Sets code description for income codes when ComboBox changes value"""
        if self.combo_income.currentText() == "0":
            self.income_desc.setText("Svi prihodi".upper())
        else:
            self.income_desc.setText((settings.get_code_desc("income", self.combo_income.currentText())).upper())
        logging.info("Income ComboBox changed value")

        self.click_btn_show()
        logging.info("Income Tree updated")

    def code_select_outcome(self):
        """Sets code description for outcome codes when ComboBox changes value"""
        if self.combo_outcome.currentText() == "0":
            self.outcome_desc.setText("Svi rashodi".upper())
        else:
            self.outcome_desc.setText((settings.get_code_desc("outcome", self.combo_outcome.currentText())).upper())
        logging.info("Outcome ComboBox changed value")

        self.click_btn_show()
        logging.info("Outcome Tree updated")

    def click_income_btn1(self):
        """Open QDialog for new income"""
        logging.info("Clicked - NOVI UNOS")
        IncomeInputDialog(parent=self)

    def click_income_btn2(self):
        """Open QDialog for making changes to selected income"""

        logging.info("Clicked - IZMIJENI")
        # Get selected row
        income_data = [i.data() for i in (self.tree_income.selectedIndexes())]
        if len(income_data) > 0:
            IncomeEditDialog(parent=self, income_data=income_data)
        else:
            logging.info("Income edit - nothing selected")
            mb = fn.popup_message(text="Nije označen red koji se mijenja", style=self.styleSheet())
            mb.exec()

    def click_income_btn3(self):
        """Delete selected entry in income tree view"""

        logging.info("Clicked - IZBRIŠI")

        # Get selected row
        income_data = [i.data() for i in self.tree_income.selectedIndexes()]
        if len(income_data) > 0:
            dlg = ConfirmDialog(title="Potvrdi brisanje", list_label=income_data, styletext=self.styleSheet())
            if dlg.exec():
                entry_id = income_data[6]
                try:
                    fn.update_database(settings.get_setting("database"), f"DELETE FROM income WHERE ID = {entry_id}")
                except Exception as err:
                    logging.critical(f"Critical error: {err}")
        else:
            fn.popup_message(text="Označi stavku za brisanje", title="Warning", style=self.styleSheet()).exec()

        self.click_btn_show()

    # Outcome button actions
    def click_outcome_btn1(self):
        """Opens new outcome entry dialog"""
        logging.info("New outcome dialog opened")
        OutcomeInputDialog(parent=self)

    def click_outcome_btn2(self):
        """Open QDialog for making changes to selected outcome"""

        logging.info("Edit outcome dialog opened")

        # Get selected row
        selected_row = [i.data() for i in self.tree_outcome.selectedIndexes()]

        # if row selected
        if len(selected_row) > 0:
            OutcomeEditDialog(parent=self, outcome_data=selected_row)
        else:
            logging.info("Outcome edit - nothing selected")
            mb = fn.popup_message(text="Nije označen red koji se mijenja", style=self.styleSheet())
            mb.exec()

    def click_outcome_btn3(self):
        """Delete selected entry in outcome tree view"""

        logging.info("Delete outcome button pressed")

        # Get selected row
        selected_row = [i.data() for i in self.tree_outcome.selectedIndexes()]

        # Delete entry by ID
        if len(selected_row) > 0:
            entry_id = selected_row[6]
            dlg = ConfirmDialog(title="Potvrdi brisanje", list_label=selected_row, styletext=self.styleSheet())
            if dlg.exec():
                try:
                    fn.update_database(settings.get_setting("database"), f"DELETE FROM outcome WHERE ID = {entry_id}")
                except Exception as err:
                    logging.critical(f"Critical error: {err}")
        else:
            fn.popup_message(text="Označi stavku za brisanje", title="Warning", style=self.styleSheet()).exec()

        self.click_btn_show()

    # Table buttons actions
    def click_browse_btn(self):
        """Browse for bank report"""

        # Open file dialog and choose bakn report file
        path = QFileDialog.getOpenFileName(self, "Open file", ".", "Izvod (*.txt)")[0]
        if path != "":
            self.file_path.setText(path)
            data, report_year = fn.decode_input_file(path)
            for row in data:
                # Income/outcome combobox
                combobox = QComboBox()
                combobox.addItems(["Prihod", "Rashod"])
                combobox.setCurrentText(str(row[0]))

                # Code combobox
                combobox_code = QComboBox()
                if row[0] == "Prihod":
                    combobox_code.addItems(settings.get_income_codes())
                elif row[0] == "Rashod":
                    combobox_code.addItems(settings.get_outcome_codes())

                # Amount with LineEdit
                amount_edit = QLineEdit(str(row[2]))
                amount_edit.setValidator(
                    QRegularExpressionValidator(QRegularExpression("\d{1,10}[.]\d\d"), amount_edit))

                # DateEdit
                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                date_edit.setDate(QDate.fromString(str(row[3]), "d.M.yyyy."))

                irow = self.io_table.rowCount()

                self.io_table.insertRow(irow)
                self.io_table.setCellWidget(irow, 0, combobox)
                self.io_table.setCellWidget(irow, 1, combobox_code)
                self.io_table.setCellWidget(irow, 3, amount_edit)
                self.io_table.setCellWidget(irow, 4, date_edit)

                self.io_table.setItem(irow, 2, QTableWidgetItem(str(row[1])))
                self.io_table.setItem(irow, 5, QTableWidgetItem(f"Izvod br. {row[4]}/{report_year}"))

    def click_add_row(self):
        """Add row to table"""

        irow = self.io_table.rowCount()
        self.io_table.insertRow(irow)

        # Add combobox and dateedit
        combobox = QComboBox()
        combobox.addItems(["Prihod", "Rashod"])
        code_cb = QComboBox()
        code_cb.addItems(settings.get_income_codes())
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        amount_edit = QLineEdit()
        amount_edit.setValidator(QRegularExpressionValidator(QRegularExpression("\d{1,10}[.]\d\d"), amount_edit))

        def code_combo_action():
            """Connects code combobox items with income/outcome combobox"""

            code_cb.clear()
            if combobox.currentText() == "Prihod":
                code_cb.addItems(settings.get_income_codes())
            else:
                code_cb.addItems(settings.get_outcome_codes())

        combobox.activated.connect(code_combo_action)

        # Add comboboxes to table
        self.io_table.setCellWidget(irow, 0, combobox)
        self.io_table.setCellWidget(irow, 1, code_cb)
        self.io_table.setCellWidget(irow, 3, amount_edit)
        self.io_table.setCellWidget(irow, 4, date_edit)

    def click_remove_row(self):
        """Remove selected row from table"""

        # Get selected row
        self.io_table.removeRow(self.io_table.currentRow())

    def click_save_btn(self):
        """Save table data to database"""

        logging.info("Income/outcome table - Save button pressed")

        # Create query for every row
        if self.io_table.rowCount() == 0:
            # If there is no data to save - popup message
            fn.popup_message("Nema podataka za spremanje!", style=self.styleSheet()).exec()
        else:
            # Get row count
            for irow in range(self.io_table.rowCount()):
                if self.io_table.cellWidget(irow, 0).currentText() == "Prihod":
                    table = "income"
                elif self.io_table.cellWidget(irow, 0).currentText() == "Rashod":
                    table = "outcome"
                else:
                    table = None

                # Put item to table
                code = self.io_table.cellWidget(irow, 1).currentText()
                code_desc = settings.get_code_desc(table, code)
                desc = self.io_table.item(irow, 2).text()
                amount = self.io_table.cellWidget(irow, 3).text()
                day = self.io_table.cellWidget(irow, 4).date().toPyDate()
                remark = self.io_table.item(irow, 5).text()
                entry_id = fn.set_id(settings.get_setting("database"), table)

                # Create query
                query = f"INSERT INTO {table}(code, code_desc, desc, amount, day, remark, id) VALUES " \
                        f"({code}, '{code_desc}', '{desc}', {amount}, '{day}', '{remark}', {entry_id})"

                # Execute query
                fn.save_data(settings.get_setting("database"), query)

                logging.info(f"Income/outcome saved to database: {query}")

            # Show dialog
            fn.popup_message("Podaci iz tablice upisani u bazu podataka", style=self.styleSheet()).exec()

            # Clear the table
            self.io_table.setRowCount(0)

            # Refresh all trees and reports
            self.click_btn_show()

            # Take care of bank report filepath
            self.file_path.setText("Odaberi izvod")

    def click_clear_btn(self):
        """Removes all rows from input/output table and changes filename"""

        self.io_table.setRowCount(0)
        self.file_path.setText("Odaberi izvod")

    @classmethod
    def create_query(cls, table, data_from, data_to, code="0"):
        """Create query for retriving data from database"""
        if code == "0":
            return f"SELECT * FROM {table} WHERE day >= '{data_from} 00:00:00' AND day <= '{data_to} 00:00:00'"
        else:
            return f"SELECT * FROM {table} WHERE day >= '{data_from} 00:00:00' AND day<= '{data_to} 00:00:00' " \
                   f"AND code = {code}"

    def create_report_data(self, date_from, date_to):
        """
        Creates list of data for creating reports

        keyword:
        QDateEdit data_from
        QDateEdit data_to

        returns: list of data
        """
        sum_income = []
        for code in settings.get_income_codes():
            if code == "13":
                continue
            total = 0.0
            code_data = fn.get_data_from_database(settings.get_setting("database"),
                                                  self.create_query("income", date_from, date_to, code))
            for icode in code_data:
                total += float(icode[3])
            sum_income.append([code, settings.get_code_desc("income", code), total])

        sum_outcome = []
        for code in settings.get_outcome_codes():
            if code == "21":
                continue
            total = 0.0
            code_data = fn.get_data_from_database(settings.get_setting("database"),
                                                  self.create_query("outcome", date_from, date_to, code))
            for icode in code_data:
                total += float(icode[3])
            sum_outcome.append([code, settings.get_code_desc("outcome", code), total])

        return sum_income, sum_outcome

    @classmethod
    def update_tree_list(cls, tree, data):
        """Puts income/outcome data into tree list"""
        tree.clear()

        for row in data:
            # Takes care of tuples
            row = list(row)

            # For trees with different column numbers
            if len(row) == 3:
                row[2] = f"{row[2]:,.2f}"
            elif len(row) == 7:
                row[3] = f"{row[3]:,.2f}"
            else:
                logging.info("FORMATING FAILED")

            # Puts data into tree widget
            QTreeWidgetItem(tree, [str(i) for i in row])

    @classmethod
    def calculate_total(cls, data):
        """Calculate sums of income/outcome"""
        total = 0.0
        for row in data:
            if len(row) == 3:
                total += float(row[2])
            elif len(row) == 7:
                total += float(row[3])
        return total

    def keyPressEvent(self, event):
        """KeyPressEvents"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_F1:
                self.setStyleSheet(fn.create_stylesheet("Default"))
                # Add link formating function
            if event.key() == Qt.Key.Key_F2:
                self.setStyleSheet(fn.create_stylesheet("BlueGreyLight"))
            if event.key() == Qt.Key.Key_F3:
                self.setStyleSheet(fn.create_stylesheet("BlueGreyDark"))
            if event.key() == Qt.Key.Key_F4:
                self.setStyleSheet(fn.create_stylesheet("WarmGrey"))
            if event.key() == Qt.Key.Key_F5:
                self.setStyleSheet(fn.create_stylesheet("CoolGrey"))
            if event.key() == Qt.Key.Key_F6:
                self.setStyleSheet(fn.create_stylesheet("DarkRed"))
            if event.key() == Qt.Key.Key_F7:
                self.setStyleSheet(fn.create_stylesheet("Green"))
        else:
            if event.key() == Qt.Key.Key_Home:
                self.tabWidget.setCurrentIndex(0)
            if event.key() == Qt.Key.Key_PageUp:
                if self.tabWidget.currentIndex() < len(self.tabWidget) - 1:
                    self.tabWidget.setCurrentIndex(self.tabWidget.currentIndex() + 1)
            if event.key() == Qt.Key.Key_PageDown:
                if self.tabWidget.currentIndex() > 0:
                    self.tabWidget.setCurrentIndex(self.tabWidget.currentIndex() - 1)
            if event.key() == Qt.Key.Key_F1:
                HelpWidget(parent=self)
            elif event.key() == Qt.Key.Key_F2:
                CodeViewer(parent=self)
            elif event.key() == Qt.Key.Key_F3:
                LogViewer(parent=self)
            elif event.key() == Qt.Key.Key_F4:
                pass
            elif event.key() == Qt.Key.Key_F5:
                if self.user_type == "Admin":
                    logging.info("Reboot aplication")
                    self.reboot()
            elif event.key() == Qt.Key.Key_F6:
                pass
            elif event.key() == Qt.Key.Key_F7:
                pass
            elif event.key() == Qt.Key.Key_F8:
                pass
            elif event.key() == Qt.Key.Key_F9:
                # Change user type
                login = LoginWidget(parent=self)
                login.exec()
                self.user_type = login.user_type
                self.setWindowTitle(f'Finance Manager v3.0 - Gimnastički klub Sokol Karlovac - {self.user_type}')
            elif event.key() == Qt.Key.Key_F10:
                # Display SplashScreen image
                dlg = QDialog(self)
                lb = QLabel(dlg)
                lb.setPixmap(QPixmap("images/splashscreen.png"))
                lb.resize(lb.pixmap().size())
                dlg.exec()
            elif event.key() == Qt.Key.Key_F11:
                # Display backup retrive window
                if self.user_type == "Admin":
                    BackUpRetriveWindow(self)
            elif event.key() == Qt.Key.Key_F12:
                if self.user_type == "Admin":
                    SettingsEdit(parent=self)
                else:
                    login = LoginWidget(parent=self)
                    login.exec()
                    self.user_type = login.user_type
                    self.setWindowTitle(f'Finance Manager v3.0 - Gimnastički klub Sokol Karlovac - {self.user_type}')

    def change_links_format(self, style="Default"):
        """Change links format"""
        # Get all links
        # Change style
        print(style)


# Income classes
class IncomeInputDialog(QDialog):
    """Dialog for new income entry"""

    def __init__(self, parent):
        """Constructor"""

        super().__init__()
        self.parent = parent
        uic.loadUi("ui/inputdialog.ui", self)
        self.setStyleSheet(parent.styleSheet())
        self.setWindowTitle("Upis prihoda")

        # Set date value to current date
        self.date.setDate(QDate(QDate.currentDate()))

        # Button actions
        self.btn_save.clicked.connect(self.click_save)
        self.btn_close.clicked.connect(lambda x: (self.close(), logging.info("New income dialog closed")))

        # Combo box
        icodes = fn.get_data_from_database(settings.file, "SELECT * FROM income")
        self.code.addItems([str(i[0]) for i in icodes])

        self.code.activated.connect(lambda: (
            self.code_desc.setText(fn.get_data_from_database(
                settings.file,
                f"SELECT * FROM income WHERE code = '{self.code.currentText()}'")[0][1])
        ))

        self.code_desc.setText(fn.get_data_from_database(
            settings.file,
            f"SELECT * FROM income WHERE code = '{self.code.currentText()}'")[0][1])

        # Set Validator - allow only numbers and decimal point
        self.amount.setValidator(QRegularExpressionValidator(QRegularExpression("\d{1,10}[.]\d\d"), self.amount))

        self.exec()

    def click_save(self):
        """Save income information to database"""

        code = self.code.currentText()
        code_desc = self.code_desc.text()
        desc = self.desc.text()
        amount = self.amount.text()
        date = self.date.date().toPyDate()
        remark = self.remark.text()
        entry_id = fn.set_id(settings.get_setting("database"), "income")

        query = f"INSERT INTO income(code, code_desc, desc, amount, day, remark, id) VALUES " \
                f"({code}, '{code_desc}', '{desc}', {amount}, '{date}', '{remark}', {entry_id})"

        # Input control
        if desc.strip() == "" or amount.strip() == "":
            mb = fn.popup_message(text="Nedostaje opis ili iznos prihoda", title="Pogrešan upis",
                                  style=self.styleSheet())
            mb.exec()
        else:
            try:
                fn.save_data(database_path=settings.get_setting("database"), query=query)
                logging.info(f"Saved to database: {query}")
            except Exception as err:
                logging.critical(f"Critical error: {err}")

            self.parent.click_btn_show()

            self.close()
            logging.info("Income saved to database")


class IncomeEditDialog(QDialog):
    """Dialog for changes in income"""

    def __init__(self, parent, income_data):
        """Constructor"""

        super().__init__()
        self.parent = parent
        uic.loadUi("ui/inputdialog.ui", self)
        self.setStyleSheet(parent.styleSheet())
        self.setWindowTitle("Promjena podataka prihoda")

        # Button actions
        self.btn_save.clicked.connect(self.click_save)
        self.btn_close.clicked.connect(lambda x: (self.close(), logging.info("New income dialog closed")))

        # Combo box

        icodes = fn.get_data_from_database(settings.file, "SELECT * FROM income")
        self.code.addItems([str(i[0]) for i in icodes])
        self.code.setCurrentText(income_data[0])

        self.code_desc.setText(fn.get_data_from_database(
            settings.file,
            f"SELECT * FROM income WHERE code = '{self.code.currentText()}'")[0][1])

        self.code.activated.connect(lambda: (
            self.code_desc.setText(fn.get_data_from_database(
                settings.file,
                f"SELECT * FROM income WHERE code = '{self.code.currentText()}'")[0][1])))

        # Amount input only numbers and decimal point
        self.amount.setValidator(QRegularExpressionValidator(QRegularExpression("\d{1,10}[.]\d\d"), self.amount))

        # Get information elements
        self.date.setDate(QDate.fromString(income_data[4], "yyyy-MM-dd"))

        # Set selected values
        self.desc.setText(income_data[2])
        self.amount.setText(income_data[3])
        self.remark.setText(income_data[5])
        self.id.setText(income_data[6])

        self.exec()

    def click_save(self):
        """Updates income information in database using ID"""

        code = self.code.currentText()
        code_desc = self.code_desc.text()
        desc = self.desc.text()
        amount = self.amount.text()
        date = self.date.date().toPyDate()
        remark = self.remark.text()
        entry_id = self.id.text()

        # Execute query using update_database function
        if desc.strip() == "" or amount.strip() == "":
            mb = fn.popup_message(text="Nedostaje opis ili iznos rashoda", title="Pogrešan upis",
                                  style=self.styleSheet())
            mb.exec()
        else:
            try:
                # Create query
                query = f"UPDATE income SET code = {code}, code_desc = '{code_desc}', desc = '{desc}', " \
                        f"amount = {amount}, day = '{date}', remark = '{remark}' WHERE id = {entry_id}"
                # Save to database
                fn.update_database(database_path=settings.get_setting("database"), query=query)
                logging.debug(f"Update made for income id = {entry_id}")
            except Exception as err:
                logging.critical(f"Critical error: {err}")

            # Update everything
            self.parent.click_btn_show()

            # Close Edit dialog
            self.close()


# Outcome classes
class OutcomeInputDialog(QDialog):
    """Dialog for new outcome entry"""

    def __init__(self, parent):
        """Constructor"""

        super().__init__()
        self.parent = parent
        uic.loadUi("ui/inputdialog.ui", self)
        self.setStyleSheet(parent.styleSheet())
        self.setWindowTitle("Upis rashoda")

        # Set date value to current date
        date = self.__getattribute__("date")
        date.setDate(QDate(QDate.currentDate()))

        # Button actions
        btn_save = self.__getattribute__("btn_save")
        btn_close = self.__getattribute__("btn_close")
        btn_save.clicked.connect(self.click_save)
        btn_close.clicked.connect(lambda x: (self.close(), logging.info("New outcome dialog closed")))

        # Combo box
        code_combo = self.__getattribute__("code")
        icodes = fn.get_data_from_database(settings.file, "SELECT * FROM outcome")
        code_combo.addItems([str(i[0]) for i in icodes])

        code_desc = self.__getattribute__("code_desc")

        code_combo.activated.connect(lambda: (
            code_desc.setText(fn.get_data_from_database(
                settings.file,
                f"SELECT * FROM outcome WHERE code = '{code_combo.currentText()}'")[0][1])
        ))

        code_desc.setText(fn.get_data_from_database(
            settings.file,
            f"SELECT * FROM outcome WHERE code = '{code_combo.currentText()}'")[0][1])

        amount = self.__getattribute__("amount")
        amount.setValidator(QRegularExpressionValidator(QRegularExpression("\d{1,10}[.]\d\d"), amount))

        self.exec()

    def click_save(self):
        """Save outcome information to database"""

        code = self.__getattribute__("code").currentText()
        code_desc = self.__getattribute__("code_desc").text()
        desc = self.__getattribute__("desc").text()
        amount = self.__getattribute__("amount").text()
        date = self.__getattribute__("date").date().toPyDate()
        remark = self.__getattribute__("remark").text()
        entry_id = fn.set_id(settings.get_setting("database"), "outcome")

        # Input control
        if desc.strip() == "" or amount.strip() == "":
            mb = fn.popup_message(text="Nedostaje opis ili iznos rashoda", title="Pogrešan upis",
                                  style=self.styleSheet())
            mb.exec()
        else:
            # Create query
            query = f"INSERT INTO outcome(code, code_desc, desc, amount, day, remark, id) VALUES " \
                    f"({code}, '{code_desc}', '{desc}', {amount}, '{date}', '{remark}', {entry_id})"
            try:
                fn.save_data(database_path=settings.get_setting("database"), query=query)
                logging.info(f"Saved to database: {query}")
            except Exception as err:
                logging.critical(f"Critical error: {err}")

            self.parent.click_btn_show()

            self.close()
            logging.info("Outocome saved to database")


class OutcomeEditDialog(QDialog):
    """Dialog for changes in outcome"""

    def __init__(self, parent, outcome_data):
        """Constructor"""

        super().__init__()
        self.parent = parent
        uic.loadUi("ui/inputdialog.ui", self)
        self.setStyleSheet(parent.styleSheet())
        self.setWindowTitle("Promjena podataka rashoda")

        # Button actions
        btn_save = self.__getattribute__("btn_save")
        btn_close = self.__getattribute__("btn_close")
        btn_save.clicked.connect(self.click_save)
        btn_close.clicked.connect(lambda x: (self.close(), logging.info("New outcome dialog closed")))

        # Combo box
        code_combo = self.__getattribute__("code")
        code_desc = self.__getattribute__("code_desc")

        icodes = fn.get_data_from_database(settings.file, "SELECT * FROM outcome")
        code_combo.addItems([str(i[0]) for i in icodes])
        code_combo.setCurrentText(outcome_data[0])

        code_desc.setText(fn.get_data_from_database(
            settings.file,
            f"SELECT * FROM outcome WHERE code = '{code_combo.currentText()}'")[0][1])

        code_combo.activated.connect(lambda: (
            code_desc.setText(fn.get_data_from_database(
                settings.file,
                f"SELECT * FROM outcome WHERE code = '{code_combo.currentText()}'")[0][1])
        ))

        # Amount input only numbers and decimal point
        amount = self.__getattribute__("amount")
        amount.setValidator(QRegularExpressionValidator(QRegularExpression("\d{1,10}[.]\d\d"), amount))

        # Get information elements
        date = self.__getattribute__("date")
        date.setDate(QDate.fromString(outcome_data[4], "yyyy-MM-dd"))

        desc = self.__getattribute__("desc")
        amount = self.__getattribute__("amount")
        remark = self.__getattribute__("remark")
        entry_id = self.__getattribute__("id")

        # Set selected values
        desc.setText(outcome_data[2])
        amount.setText(outcome_data[3])
        remark.setText(outcome_data[5])
        entry_id.setText(outcome_data[6])

        self.exec()

    def click_save(self):
        """Updates income information in database using ID"""

        code = self.__getattribute__("code").currentText()
        code_desc = self.__getattribute__("code_desc").text()
        desc = self.__getattribute__("desc").text()
        amount = self.__getattribute__("amount").text()
        date = self.__getattribute__("date").date().toPyDate()
        remark = self.__getattribute__("remark").text()
        entry_id = self.__getattribute__("id").text()

        # Execute query using update_database function
        if desc.strip() == "" or amount.strip() == "":
            mb = fn.popup_message(text="Nedostaje opis ili iznos rashoda", title="Pogrešan upis",
                                  style=self.styleSheet())
            mb.exec()
        else:
            try:
                # Create query
                query = f"UPDATE outcome SET code = {code}, code_desc = '{code_desc}', desc = '{desc}', " \
                        f"amount = {amount}, day = '{date}', remark = '{remark}' WHERE id = {entry_id}"
                # Save to database
                fn.update_database(database_path=settings.get_setting("database"), query=query)
                logging.debug(f"Update made for outcome id = {entry_id}")
            except Exception as err:
                logging.critical(f"Critical error: {err}")

            # Update everything
            self.parent.click_btn_show()

            # Close Edit dialog
            self.close()


# F1
class HelpWidget(QDialog):
    """Dialog with some help information"""

    def __init__(self, parent):
        """Constructor"""

        super().__init__()
        uic.loadUi("ui/help.ui", self)

        self.setStyleSheet(parent.styleSheet())
        self.setWindowTitle("Pomoć")
        self.set_text()
        self.showMaximized()
        self.exec()

    def set_text(self, file="bin/help.txt"):
        """Load text from file"""

        with open(file, 'r', encoding="utf8") as f:
            text = f.read()

            self.textBrowser.setText(text)


# F2
class CodeViewer(QDialog):
    """Shows income and outcome codes and descriptions"""

    def __init__(self, parent):
        """Constructor"""

        super().__init__()
        uic.loadUi("ui/codeviewer.ui", self)
        self.setStyleSheet(parent.styleSheet())

        income_tree = self.__getattribute__("tree_income")
        outcome_tree = self.__getattribute__("tree_outcome")

        icodes = fn.get_data_from_database(settings.file, "SELECT * FROM income")
        ocodes = fn.get_data_from_database(settings.file, "SELECT * FROM outcome")

        income_tree.clear()
        for ic in icodes:
            QTreeWidgetItem(income_tree, [str(i) for i in ic])

        outcome_tree.clear()
        for oc in ocodes:
            QTreeWidgetItem(outcome_tree, [str(i) for i in oc])

        btn_close = self.__getattribute__("btn_close")
        btn_close.clicked.connect(lambda _: (self.close(), logging.info("CodeViewer closed")))

        self.showMaximized()
        self.exec()


# F3
class LogViewer(QDialog):
    """Read log file"""

    def __init__(self, parent):
        super().__init__()
        uic.loadUi("ui/logview.ui", self)
        self.setStyleSheet(parent.styleSheet())
        self.setWindowTitle("Log view")

        with open(settings.get_setting("log_filename"), "r") as log:
            text = log.read()

        text_browser = self.__getattribute__("textBrowser")
        text_browser.append(text)

        self.showMaximized()
        self.exec()


# F12
class SettingsEdit(QDialog):
    """Edit settings"""

    def __init__(self, parent):
        super().__init__(parent=parent)
        uic.loadUi("ui/configedit.ui", self)
        self.setWindowTitle("Settings edit")

        # Button actions
        self.browse_db.clicked.connect(self.set_db)
        self.browse_log.clicked.connect(self.set_log)
        self.save_btn.clicked.connect(self.save_settings)
        self.close_btn.clicked.connect(self.click_close)

        self.btn_database.clicked.connect(self.action_db)
        self.btn_log.clicked.connect(self.action_log)
        self.btn_settings.clicked.connect(self.action_set)
        self.btn_task.clicked.connect(self.action_task)

        # Load settings
        self.load_settings_from_db()

        # Execute QDialog
        self.exec()

    def load_settings_from_db(self):
        """Load current settings from database and display in dialog"""

        # Load settings from database
        settings_from_db = fn.get_data_from_database(settings.file, "SELECT * FROM settings")

        self.db_path.setText(settings_from_db[0][1])
        self.log_path.setText(settings_from_db[1][1])
        self.log_level.setCurrentText(settings_from_db[2][1])
        self.log_format.setText(settings_from_db[3][1])
        self.last_modified.setDate(QDate.fromString(settings_from_db[6][1], "d.M.yyyy."))
        self.version.setText(settings_from_db[5][1])
        self.style.setCurrentText(settings_from_db[7][1])

        # Get Functions / Tabs
        self.graphics.setChecked(bool(int(settings_from_db[8][1])))
        self.statistics.setChecked(bool(int(settings_from_db[9][1])))
        self.income.setChecked(bool(int(settings_from_db[10][1])))
        self.outcome.setChecked(bool(int(settings_from_db[11][1])))
        self.report.setChecked(bool(int(settings_from_db[12][1])))
        self.table.setChecked(bool(int(settings_from_db[13][1])))
        self.bills.setChecked(bool(int(settings_from_db[14][1])))

    def save_settings(self):
        """Save settings from dialog"""

        # Save every setting
        try:
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{self.db_path.text()}' WHERE setting='database'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{self.log_path.text()}' WHERE setting='log_filename'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{self.log_level.currentText()}' WHERE setting='log_level'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{self.log_format.text()}' WHERE setting='log_format'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{self.version.text()}' WHERE setting='version'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{self.last_modified.text()}' WHERE setting='last_modified'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{self.style.currentText()}' WHERE setting='style'")

            # Functions
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{1 if self.graphics.isChecked() else 0}'"
                               f"WHERE setting='graphics'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{1 if self.statistics.isChecked() else 0}'"
                               f"WHERE setting='statistics'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{1 if self.income.isChecked() else 0}'"
                               f"WHERE setting='income'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{1 if self.outcome.isChecked() else 0}'"
                               f"WHERE setting='outcome'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{1 if self.report.isChecked() else 0}'"
                               f"WHERE setting='report'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{1 if self.table.isChecked() else 0}'"
                               f"WHERE setting='table'")
            fn.update_database(settings.file,
                               f"UPDATE settings SET value='{1 if self.bills.isChecked() else 0}'"
                               f"WHERE setting='bills'")

            logging.info("Settings saved to database")
        except Exception as error:
            logging.error(f"Error occured while saving settings to database: {error}")

        # Close Settings Dialog when saved
        self.close()

        # Reboot App - loads new settings
        self.parent().reboot()

    def set_db(self):
        """Set database file"""
        filepath = QFileDialog.getOpenFileName(self, "Open file", ".", "Database (*.sqlite *.db)")
        if filepath[0] != "":
            self.db_path.setText(filepath[0])

    def set_log(self):
        """Set log file"""
        path = self.__getattribute__("log_path")
        filepath = QFileDialog.getOpenFileName(self, "Open file", ".", "Log file (*.txt *.dat)")
        if filepath[0] != "":
            path.setText(filepath[0])

    # Button Actions
    def action_db(self):
        """Download database file from Dropbox"""

        try:
            download_database("/database.sqlite", "backup/backup_database.db", token)
            popup_message("Database retrived from Dropbox").exec()
            logging.info("Database retrived from Dropbox")
        except ConnectionError:
            popup_message("Error occured while retriving database file from Dropbox. Check internet connection!").exec()
            logging.info("Error occured while retriving database file from Dropbox. Check internet connection!")

    def action_log(self):
        """Download log file from Dropbox"""
        try:
            download_database("/log.txt", "backup/backup_log.txt", token)
            popup_message("Log file retrived from Dropbox").exec()
            logging.info("Log file retrived from Dropbox")
        except ConnectionError:
            popup_message("Error occured while retriving log file from Dropbox. Check internet connection!").exec()
            logging.info("Error occured while retriving log file from Dropbox. Check internet connection!")

    def action_set(self):
        """Download settings file from Dropbox"""
        try:
            download_database("/settings.db", "backup/backup_settings.db", token)
            popup_message("Settings file retrived from Dropbox").exec()
            logging.info("Settings file retrived from Dropbox")
        except ConnectionError:
            popup_message("Error occured while retriving settings file from Dropbox. Check internet connection!").exec()
            logging.info("Error occured while retriving settings file from Dropbox. Check internet connection!")

    def action_task(self):
        """Download Task list from Dropbox"""
        try:
            download_database("/taskList.db", "backup/backup_taskList.db", token)
            popup_message("Task list retrived from Dropbox").exec()
            logging.info("Task list retrived from Dropbox")
        except ConnectionError:
            popup_message("Error occured while retriving Task list from Dropbox. Check internet connection!").exec()
            logging.info("Error occured while retriving Task list file from Dropbox. Check internet connection!")

    def click_close(self):
        """Close dialog"""
        logging.info("Setting Dialog closed")
        self.close()
