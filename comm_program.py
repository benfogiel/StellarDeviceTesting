"""Main module for the comm_program package."""

import sys
from PyQt5.QtWidgets import QApplication
from comm_program.gui.gui import MainGui


def main() -> None:
    """Run the comm_program package."""
    app = QApplication(sys.argv)
    main_win = MainGui()
    main_win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
