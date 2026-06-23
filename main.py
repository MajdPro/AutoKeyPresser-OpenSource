import os
import sys

# Completely silence all Qt warnings and DPI errors in the console
os.environ["QT_LOGGING_RULES"] = "*.warning=false;*.error=false"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

import threading
import time
from PyQt6 import QtWidgets, QtCore, QtGui
import pyautogui
import keyboard  # Reliable global hotkey handler

# Eliminate pyautogui's default 100ms delay limit for true millisecond speed
pyautogui.PAUSE = 0

SYSTEM_SHORTCUT_KEYS = ["f1", "f3", "f4", "f7", "f10", "cmd", "win", "alt", "tab", "escape"]

class KeyCaptureLineEdit(QtWidgets.QLineEdit):
    hotkey_changed = QtCore.pyqtSignal(str)

    def __init__(self, default_text="", parent=None):
        super().__init__(default_text, parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click here and press any key...")
        self.key_name = default_text.lower()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        
        if key == QtCore.Qt.Key.Key_F1:
            display_text = "f1"
            event.accept()
        elif key == QtCore.Qt.Key.Key_Space:
            display_text = "space"
        elif key == QtCore.Qt.Key.Key_Control:
            display_text = "ctrl"
        elif key == QtCore.Qt.Key.Key_Shift:
            display_text = "shift"
        elif key == QtCore.Qt.Key.Key_Alt:
            display_text = "alt"
        elif key == QtCore.Qt.Key.Key_Meta:
            display_text = "win"
        else:
            display_text = event.text().strip().lower()
            if not display_text:
                display_text = QtGui.QKeySequence(key).toString().lower()

        if display_text:
            self.setText(display_text)
            self.key_name = display_text
            self.hotkey_changed.emit(display_text)
            self.clearFocus()


class KeyPresser(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.current_hotkey = "z"
        self.init_ui()
        
        # KEY CHANGES HERE: Use suppressed global hooks to allow background triggering
        keyboard.add_hotkey(self.current_hotkey, self.toggle_state, suppress=False)

    def init_ui(self):
        self.setWindowTitle("Auto Key Presser")
        
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        scale_factor = max(1.0, screen_width / 1920.0)
        
        window_w = int(450 * scale_factor)
        window_h = int(420 * scale_factor)
        font_size = int(13 * scale_factor)
        padding_size = int(8 * scale_factor)
        
        self.setGeometry(int((screen_width - window_w) / 2), int((screen_height - window_h) / 3), window_w, window_h)
        
        self.setStyleSheet(f"""
            QWidget {{ background-color: #1e1e1e; color: white; font-size: {font_size}px; }}
            QLabel {{ font-weight: 500; margin-top: {int(4*scale_factor)}px; }}
            QPushButton {{ background-color: #2d89ef; padding: {padding_size}px; border-radius: 6px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #1b5fbf; }}
            QLineEdit {{ background-color: #2b2b2b; padding: {padding_size}px; border-radius: 4px; border: 1px solid #3c3c3c; color: #00ffcc; }}
            QLineEdit:focus {{ border: 1px solid #2d89ef; background-color: #333333; }}
        """)

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(int(8 * scale_factor))
        layout.setContentsMargins(int(15 * scale_factor), int(15 * scale_factor), int(15 * scale_factor), int(15 * scale_factor))

        self.key_input = KeyCaptureLineEdit("space")
        
        # NUMBERS ONLY VALIDATOR
        self.delay_input = QtWidgets.QLineEdit("100")
        int_validator = QtGui.QIntValidator(1, 99999, self)
        self.delay_input.setValidator(int_validator)
        
        self.toggle_key_input = KeyCaptureLineEdit("z")
        self.toggle_key_input.hotkey_changed.connect(self.update_hotkey)
        
        self.status = QtWidgets.QLabel("Status: Stopped")
        self.status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet(f"font-size: {int(font_size * 1.1)}px; font-weight: bold; color: #aaaaaa;")

        self.warning_label = QtWidgets.QLabel("")
        self.warning_label.setWordWrap(True)
        self.warning_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.warning_label.setStyleSheet("color: #ff3333; font-weight: bold; padding: 2px;")

        self.start_btn = QtWidgets.QPushButton("Start")
        self.stop_btn = QtWidgets.QPushButton("Stop")

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

        layout.addWidget(QtWidgets.QLabel("Target Key to Press (Click & Tap Key):"))
        layout.addWidget(self.key_input)
        layout.addWidget(QtWidgets.QLabel("Delay Between Presses (Milliseconds - Numbers Only):"))
        layout.addWidget(self.delay_input)
        layout.addWidget(QtWidgets.QLabel("Global Toggle Hotkey (Starts & Stops):"))
        layout.addWidget(self.toggle_key_input)
        
        layout.addSpacing(int(10 * scale_factor))
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.status)
        layout.addWidget(self.warning_label)

        self.setLayout(layout)

    def update_hotkey(self, key_str):
        try:
            keyboard.remove_hotkey(self.current_hotkey)
        except:
            pass
        
        self.current_hotkey = key_str
        # Dynamic global hook tracking update
        keyboard.add_hotkey(self.current_hotkey, self.toggle_state, suppress=False)
        
        if key_str in SYSTEM_SHORTCUT_KEYS:
            self.warning_label.setText(f"⚠️ Warning: '{key_str.upper()}' is often used by Windows shortcuts. If behavior acts strange, switch hotkeys.")
        else:
            self.warning_label.setText("")

    def toggle_state(self):
        if self.running:
            QtCore.QMetaObject.invokeMethod(self, "stop", QtCore.Qt.ConnectionType.QueuedConnection)
        else:
            QtCore.QMetaObject.invokeMethod(self, "start", QtCore.Qt.ConnectionType.QueuedConnection)

    def press_loop(self):
        while self.running:
            try:
                key = self.key_input.text().strip()
                delay_text = self.delay_input.text()
                delay_ms = float(delay_text) if delay_text else 100.0
                delay = delay_ms / 1000.0
                
                pyautogui.press(key)
                if delay > 0:
                    time.sleep(delay)
            except:
                time.sleep(0.01)

    @QtCore.pyqtSlot()
    def start(self):
        if not self.running:
            self.running = True
            self.status.setText("Status: Running")
            self.status.setStyleSheet(self.status.styleSheet().replace("#aaaaaa", "#00ffcc"))
            threading.Thread(target=self.press_loop, daemon=True).start()

    @QtCore.pyqtSlot()
    def stop(self):
        if self.running:
            self.running = False
            self.status.setText("Status: Stopped")
            self.status.setStyleSheet(self.status.styleSheet().replace("#00ffcc", "#aaaaaa"))

    def closeEvent(self, event):
        keyboard.unhook_all()
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = KeyPresser()
    window.show()
    sys.exit(app.exec())