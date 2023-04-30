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

from comm_program.gui.selected_device import SelectedDevice


class MainGui(QMainWindow):
    """Main GUI for the Stellar Test Program."""

    def __init__(self) -> None:
        """The constructor for the MainGui class."""
        super().__init__()

        self.setWindowTitle("Rocket Lab's Stellar Test Program")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.build_top_layout()
        self.build_device_layout()

        self.central_widget.setLayout(self.layout)

    def build_top_layout(self) -> None:
        """Build the top layout for the GUI."""
        self.device_dropdown = QComboBox()
        self.add_device_button = QPushButton("Add Device")
        self.delete_device_button = QPushButton("Delete Device")

        self.add_device_button.clicked.connect(self.add_device)
        self.delete_device_button.clicked.connect(self.delete_device)

        self.device_dropdown.currentIndexChanged.connect(self.switch_device)

        self.devices = {}

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Device:"))
        top_layout.addWidget(self.device_dropdown)
        top_layout.addWidget(self.add_device_button)
        top_layout.addWidget(self.delete_device_button)
        top_layout.setAlignment(Qt.AlignLeft)

        self.layout.addLayout(top_layout)

    def build_device_layout(self) -> None:
        """Build the device layout for the GUI."""
        self.device_layout = QVBoxLayout()
        self.layout.addLayout(self.device_layout)

    def add_device(self) -> None:
        """Add a device to the GUI."""
        device_name, add = QInputDialog.getText(self, "Add Device", "Device name:")
        if add and device_name:
            if device_name not in self.devices:
                device_tab = SelectedDevice(self)
                self.devices[device_name] = device_tab
                self.device_dropdown.addItem(device_name)
                self.device_dropdown.setCurrentText(device_name)
            else:
                QMessageBox.warning(
                    self, "Error", "This device name is already in use."
                )

    def delete_device(self) -> None:
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

    def switch_device(self) -> None:
        """Switch the device tab in the GUI."""
        device_name = self.device_dropdown.currentText()
        if device_name in self.devices:
            device_tab = self.devices[device_name]

            # Remove the current widgets from the layout
            for item in (
                self.device_layout.takeAt(0) for _ in range(self.device_layout.count())
            ):
                if item.widget().hide() is not None:
                    self.device_layout.removeItem(item)

            # Add the new widgets to the layout
            self.device_layout.addWidget(device_tab)
            device_tab.show()
