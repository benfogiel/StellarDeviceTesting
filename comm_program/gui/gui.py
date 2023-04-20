"""Main GUI for the Stellar Test Program."""

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QPushButton,
    QMessageBox,
    QInputDialog,
)
from PyQt5.QtCore import Qt

from .selected_device import SelectedDevice


class MainGUI(QMainWindow):
    def __init__(self):
        """The constructor for the MainGUI class."""
        super().__init__()

        self.setWindowTitle("Rocket Lab's Stellar Test Program")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.build_device_bar()

        self.central_widget.setLayout(self.layout)

    def build_device_bar(self):
        """Build the device bar for the GUI."""
        self.device_dropdown = QComboBox()
        self.add_device_button = QPushButton("Add Device")
        self.delete_device_button = QPushButton("Delete Device")

        self.add_device_button.clicked.connect(self.add_device)
        self.delete_device_button.clicked.connect(self.delete_device)

        self.device_dropdown.currentIndexChanged.connect(self.switch_device)

        self.devices = {}

        self.device_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Device:"))
        top_layout.addWidget(self.device_dropdown)
        top_layout.addWidget(self.add_device_button)
        top_layout.addWidget(self.delete_device_button)
        top_layout.setAlignment(Qt.AlignLeft)

        self.layout.addLayout(top_layout)
        self.layout.addLayout(self.device_layout)

    def add_device(self):
        """Add a device to the GUI."""
        device_name, ok = QInputDialog.getText(self, "Add Device", "Device name:")
        if ok and device_name:
            if device_name not in self.devices:
                device_tab = SelectedDevice()
                self.devices[device_name] = device_tab
                self.device_dropdown.addItem(device_name)
                self.device_dropdown.setCurrentText(device_name)
            else:
                QMessageBox.warning(
                    self, "Error", "This device name is already in use."
                )

    def delete_device(self):
        """Delete a device from the GUI."""
        device_name = self.device_dropdown.currentText()
        if device_name in self.devices:
            reply = QMessageBox.question(
                self,
                "Delete Device",
                f"Are you sure you want to delete device '{device_name}'?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                # Remove the current widgets from the layout
                while self.device_layout.count():
                    item = self.device_layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.hide()
                    self.device_layout.removeItem(item)
                self.devices.pop(device_name)
                index = self.device_dropdown.findText(device_name)
                self.device_dropdown.removeItem(index)
                self.switch_device()

    def switch_device(self):
        """Switch the device tab in the GUI."""
        device_name = self.device_dropdown.currentText()
        if device_name in self.devices:
            device_tab = self.devices[device_name]

            # Remove the current widgets from the layout
            while self.device_layout.count():
                item = self.device_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.hide()
                self.device_layout.removeItem(item)

            # Add the new widgets to the layout
            self.device_layout.addWidget(device_tab)
            device_tab.show()
