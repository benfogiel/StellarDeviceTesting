"""This module contains the SelectedDevice class."""

from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout

from .tab_connect import ConnectTab
from .tab_test import TestTab
from ..device_client import DeviceClient


class SelectedDevice(QWidget):
    def __init__(self):
        """The constructor for the SelectedDevice class."""
        super().__init__()

        self.connected_device = None
        self.test_thread = None
        self.run_test_button = (
            None  # used to disable button when device is not connected
        )

        # Create the tabs
        self.connect_tab = ConnectTab(self)
        self.test_tab = TestTab(self)

        # Create the QTabWidget
        self.tab_widget = QTabWidget()

        # Add the tabs to the QTabWidget
        self.tab_widget.addTab(self.connect_tab, "Connect")
        self.tab_widget.addTab(self.test_tab, "Test")

        # Set the layout for the Device class
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def connect_device(self, device_ip, device_port):
        """Discover and Connect to a device.

        Args:
            device_ip (str): The IP address of the device.
            device_port (int): The port of the device.
        """
        self.connected_device = DeviceClient(device_ip, device_port)
        # Discover the device
        discover_resp = self.connected_device.discover()
        if not discover_resp:
            print(f"Device not found.")
            self.connected_device = None

    def disconnect_device(self):
        """Disconnect from the device."""
        if self.connected_device is not None:
            self.connected_device.disconnect()
            self.connected_device = None
