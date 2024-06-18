"""
Finance Manager v3.0
Application for money income and outcome tracking
and easy one click reports creating.
"""

# pylint: disable=fixme
# pylint: disable=line-too-long

import sys
import logging
from traceback import format_exception
from PyQt6.QtWidgets import QApplication
from functions import load_logging_settings
from UserInterface import UI


def excepthook(etype, value, traceback) -> None:
    """
    Set standard output for errors to log file - Do this only for exe version of program!!
    """
    logging.critical("Critical error occurred!")
    msg = "".join(format_exception(etype, value, traceback))
    logging.critical(msg)


if __name__ == '__main__':
    # Logging setup - see "config.json"
    FILE, LEVEL, FORMAT = load_logging_settings(path="bin/settings.db")
    logging.basicConfig(filename=FILE, level=LEVEL, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    # Logging unhandled errors to file not console - commented for debugging
    sys.excepthook = excepthook

    # Run app
    logging.info("Application started!")
    app = QApplication(sys.argv)
    window = UI()
    sys.exit(app.exec())

# Bugs
# TODO: Error report dialog
# TODO: Backup files on Dropbox - use refresh token
# (https://stackoverflow.com/questions/70641660/how-do-you-get-and-use-a-refresh-token-for-the-dropbox-api-python-3-x)
# TODO: Help Window - write some help (Croatian) in file
# TODO: Overload F2 on io_table - F2 should open codes
# TODO: Code too slow... speed up

# New Features
# TODO: Kontrola broja izvoda po godinama - novi widget (godina, ukupni broj izvoda) -> listu nedostajućih izvoda
# TODO: Bug report window
# TODO: Baza podataka za izdavanje računa - pravne i/ili fizičke osobe
# TODO: Pretraživač računa (Serach)
# TODO: Izvoz računa u PDF format
# TODO: Inicijalizacija aplikacije - provjera dostupnih datoteka i direktorija - IMPORTANT
# TODO: Financijski plan
# TODO: Evidencija zaposlenih - vrsta ugovora, trajanje, potvrda o ne kažnjavanju, uvjerenje o obrazovanju
#       povezati s kalendarom da daje upozorenja
# TODO: Bilježenje događaja u kalendaru (Dodati opciju opisa)
# TODO: Export događaja u tablicu
# TODO: Administrator Window (Settings Window) - all settings, admin task, ... at one place

# New functions
# TODO: Add logging on everything
# TODO: LogViewer - add filter and clear function
# TODO: Remove income/outcome buttons - add right mouse click instead - HARD??
# TODO: Create own style
# TODO: Finance planning - income and outcome planning by code

# Style fix
# TODO: Switch title with club name and logo
# TODO: Add logo and icons

# E:\Python\Python310\Scripts\pyinstaller.exe --clean --onefile --name "Finance Manager III" --noconsole main.py
# E:\Python\Python310\Scripts\pyinstaller.exe --clean --onefile --name "Finance Manager III" --noconsole --upx-dir "E:\PythonProject\pyqt - Finance Statistic v1\bin\upx-4.0.2-win64" main.py
