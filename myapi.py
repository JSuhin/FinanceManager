from flask import Flask, request, jsonify, send_file
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.uic import loadUi
from PyQt6.QtGui import QTextCursor, QIcon
import sys
import socket


"""
To implemen RestAPI to Finance Manager:
    1. Set files path from settings
"""


class MySignalEmitter(QObject):
    custom_signal = pyqtSignal(str)

    def emit_msg(self, msg):
        self.custom_signal.emit(msg)


class FlaskThread(QThread):
    """Flask API"""

    # TODO: GET endpoints: readme/help, incomes, outcomes, settings
    # TODO: POST endpoints: addincome, addoutcome
    # TODO: PATCH endpoints: income, outcome
    # TODO: DELETE endpoints: income, outcome

    def __init__(self):
        super().__init__()
        self.app = Flask(__name__)

        self.signal = MySignalEmitter()

        @self.app.before_request
        def handle_request():
            self.signal.emit_msg(f"Request made from IP: {request.remote_addr}")

        @self.app.route('/', methods=["GET"])
        def hello():
            self.signal.emit_msg(f"--> {request.base_url}")
            return 'Finance Manager - RestFul API! For help go to "/help"'

        # Readme route

        # Download routs
        @self.app.route("/download-database")
        def database():
            """Download database"""
            try:
                self.signal.emit_msg(f"--> {request.base_url}")
                path = "bin/GKSokol.sqlite"
                return send_file(path, as_attachment=True), 200
            except Exception as e:
                self.signal.emit_msg("--> Error database could not be sent")
                return f"Error downloading file: {e}"

        @self.app.route("/download-log")
        def log():
            """Downloads log file"""
            self.signal.emit_msg(f"--> {request.base_url}")
            path = "bin/log.txt"
            return send_file(path, as_attachment=True), 200

        @self.app.route("/download-settings")
        def settings():
            """Download settings file"""
            self.signal.emit_msg(f"--> {request.base_url}")
            path = "bin/settings.db"
            return send_file(path, as_attachment=True), 200

        # GET routs
        @self.app.route("/incomes", methods=['GET', 'POST'])
        def incomes():
            # Get parameters
            params = request.args
            if request.method == "GET":
                return "GET"
            elif request.method == "POST":
                try:
                    data = request.get_json()
                    print(data)
                except Exception as e:
                    print("Exception")
                    print(e)
                return "POST"
            elif request.method == "PATCH":
                return "PATCH"
            elif request.method == "DELETE":
                return "DELETE"
            else:
                return "Invalid request", 405

            return jsonify(params)

        # POST routs

        # DELETE routs

        # PATCH routs

    def run(self):
        try:
            self.app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)  # Disable Flask's reloader
        except Exception as e:
            print(f"Error starting Flask API: {e}")


class ApiWidget(QWidget):
    """Widget"""

    def __init__(self):
        # Load interface
        super(ApiWidget, self).__init__()
        loadUi("ui/api.ui", self)

        # Add Icon
        self.setWindowIcon(QIcon('images/fm_api_logo.png'))

        self.textEditStatus.setReadOnly(True)

        # API
        self.flask_thread = FlaskThread()
        self.flask_thread.signal.custom_signal.connect(self.update_status)

        # Add action to buttons
        self.btn_start_api.clicked.connect(self.start_api)
        self.btn_exit.clicked.connect(self.close)

        # Get hostname and local IP adress
        self.hostname, self.local_ip = self.get_hostname_ip()

        self.label_host.setText(self.hostname)
        self.label_ip.setText(self.local_ip)

        self.show()

    def start_api(self):
        self.flask_thread.start()
        self.btn_start_api.setEnabled(False)
        self.update_status("API started - you can now use RestFul API")

    def get_hostname_ip(self):
        try:
            hostname = socket.gethostname()
            ip_addr = socket.gethostbyname(hostname)
            return hostname, ip_addr
        except socket.error as e:
            print(f"Error getting hostname and IP: {e}")

    def update_status(self, add_text):
        cursor = self.textEditStatus.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.textEditStatus.append(f"{add_text:<150s}")

        block_format = cursor.blockFormat()
        block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_format)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    widget = ApiWidget()
    sys.exit(app.exec())
