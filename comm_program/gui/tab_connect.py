"""This module contains the ConnectTab class which is used to connect to a device."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QIntValidator, QRegExpValidator


class ConnectTab(QWidget):
    def __init__(self, device):
        """The constructor for the ConnectTab class.

        Args:
            device (SelectedDevice): The device to connect to.
        """
        super().__init__()
        self.device = device
        self.build_connect_tab()
        self.setMaximumSize(350, 150)

    def build_connect_tab(self):
        """Build the connect tab and add it to the layout"""
        self.layout = QVBoxLayout()

        self.connection_status = QLabel("Status: Disconnected")
        self.layout.addWidget(self.connection_status)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter device IP address")
        # Set the input validator for the ip_input
        ip_pattern = QRegExp(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^localhost$"
        )
        ip_validator = QRegExpValidator(ip_pattern)
        self.ip_input.setValidator(ip_validator)

        self.layout.addWidget(self.ip_input)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter device Port")
        # Set the input validator for the port_input
        port_validator = QIntValidator(1, 65535)
        self.port_input.setValidator(port_validator)
        self.layout.addWidget(self.port_input)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_device)
        self.layout.addWidget(self.connect_button)

        self.setLayout(self.layout)

    def connect_device(self):
        """Connect to the device."""
        if (
            self.connect_button.text() == "Connect"
            and self.ip_input.text()
            and self.port_input.text()
        ):
            self.device.connect_device(
                self.ip_input.text(), int(self.port_input.text())
            )

            connected_device = self.device.connected_device
            if connected_device:
                self.connection_status.setText(
                    "Status: Connected to: "
                    + connected_device.device_model
                    + " (" + connected_device.device_serial_num + ")"
                )
                self.connect_button.setText("Disconnect")
                self.device.run_test_button.setEnabled(True)
                return
            else:
                self.connection_status.setText("Status: Connection failed")
        elif self.connect_button.text() == "Disconnect":
            self.device.disconnect_device()
            self.connection_status.setText("Status: Disconnected")
            self.connect_button.setText("Connect")
        self.device.run_test_button.setEnabled(False)
