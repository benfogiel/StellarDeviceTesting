"""This module contains the SelectedDevice class."""

from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QMessageBox

from comm_program.gui.tab_connect import ConnectTab
from comm_program.gui.tab_test import TestTab
from comm_program.device_client import DeviceClient


class SelectedDevice(QWidget):
    """This class represents the selected device."""

    def __init__(self, main_gui) -> None:
        """The constructor for the SelectedDevice class.

        Args:
            main_gui (MainGui): The MainGui instance.
        """
        super().__init__()
        self.main_gui = main_gui

        self.connected_device = None
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

    def connect_device(self, device_ip: str, device_port: int) -> None:
        """Connects to a device a device.

        Args:
            device_ip (str): The IP address of the device
            device_port (int): The port of the device
        """
        # Check if the device is already connected
        existing_device = self.already_connected_device(device_ip, device_port)
        if existing_device:
            QMessageBox.warning(
                self, "Error", f"{existing_device} is already connected to this device."
            )
            return
        self.connected_device = DeviceClient(device_ip, device_port)
        # Discover the device
        discover_resp = self.connected_device.discover()
        if not discover_resp:
            print(f"Device not found ({device_ip}:{device_port})")
            self.connected_device = None

    def disconnect_device(self):
        """Disconnect from the device."""
        if self.connected_device is not None:
            self.connected_device.disconnect()
            self.connected_device = None
        self.connect_tab.connection_status.setText("Status: Disconnected")
        self.connect_tab.connect_button.setEnabled(True)
        self.connect_tab.disconnect_button.setEnabled(False)
        self.connect_tab.device.run_test_button.setEnabled(False)

    def already_connected_device(self, device_ip: str, device_port: int) -> str:
        """Check if the device is already connected.

        Args:
            device_ip (str): The IP address of the device.
            device_port (int): The port of the device.

        Returns:
            str: The name of the device if it is already connected, otherwise None.
        """
        for device in self.main_gui.devices:
            device_tab = self.main_gui.devices[device]
            if (
                device_tab.connected_device
                and device_tab.connected_device.ip == device_ip
                and device_tab.connected_device.port == device_port
            ):
                return device
        return None

    def device_not_responding(self) -> None:
        """Prompt the user that the device is not responding
        and disconnect from the device."""
        QMessageBox.warning(
            self,
            "Error",
            "Device is not responding. Please reconnect to the device.",
        )
        self.disconnect_device()

    def start_device_test(self, test_duration: float, rate: float) -> bool:
        """Starts testing the connected device.

        Args:
            test_duration (float): The duration of the test in seconds.
            rate (float): The rate of the test in ms.

        Returns:
            bool: True if the test was started successfully, otherwise False.
        """

        # Start the test
        response = self.connected_device.start_test(test_duration, rate)
        if response[0] == -1:
            # device has been disconnected
            self.device_not_responding()
            return False
        return True

    def stop_device_test(self) -> None:
        """Stops testing the connected device."""
        response = self.connected_device.stop_test()
        if response[0] == -1:
            # device has been disconnected
            self.device_not_responding()
            return
