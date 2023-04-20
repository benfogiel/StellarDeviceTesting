"""Main module for the comm_program package."""

from PyQt5.QtWidgets import QApplication
import sys

from .gui import gui


def comm_program():
    """Main function for the comm_program package."""

    app = QApplication(sys.argv)

    main_win = gui.MainGUI()
    main_win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    comm_program()
