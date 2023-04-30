"""This module contains the ConnectTab class which is used to connect to a device."""

from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtGui import QIntValidator

if TYPE_CHECKING:
    from comm_program.gui.selected_device import SelectedDevice


class ConnectTab(QWidget):
    """This class represents the connect tab."""

    def __init__(self, device: "SelectedDevice") -> None:
        """The constructor for the ConnectTab class.

        Args:
            device (SelectedDevice): The device to connect to.
        """
        super().__init__()
        self.device = device
        self.build_connect_tab()
        self.setMaximumSize(350, 200)

    def build_connect_tab(self) -> None:
        """Build the connect tab and add it to the layout"""
        self.layout = QVBoxLayout()

        self.connection_status = QLabel("Status: Disconnected")
        self.layout.addWidget(self.connection_status)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter device IP address")

        self.layout.addWidget(self.ip_input)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter device Port")
        # Set the input validator for the port_input
        port_validator = QIntValidator(1, 65535)
        self.port_input.setValidator(port_validator)
        self.layout.addWidget(self.port_input)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect)
        self.layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.on_disconnect)
        self.disconnect_button.setEnabled(False)
        self.layout.addWidget(self.disconnect_button)

        self.setLayout(self.layout)

    def on_connect(self) -> None:
        """Handle the 'Connect' event."""
        device_ip = self.ip_input.text()
        device_port = self.port_input.text()

        if device_ip and device_port:
            self.device.connect_device(device_ip, int(device_port))
            connected_device = self.device.connected_device
            if connected_device:
                self.connection_status.setText(
                    f"Status: Connected to: {connected_device.device_model}"
                    + f"({connected_device.device_serial_num})"
                )
                self.connect_button.setEnabled(False)
                self.disconnect_button.setEnabled(True)
                self.device.run_test_button.setEnabled(True)
            else:
                self.connection_status.setText("Status: Connection failed")

    def on_disconnect(self) -> None:
        """Handle the 'Disconnect' event"""
        self.device.disconnect_device()
