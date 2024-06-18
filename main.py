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
    # sys.excepthook = excepthook

    # Run app
    logging.info("Application started!")
    app = QApplication(sys.argv)
    window = UI()
    sys.exit(app.exec())


