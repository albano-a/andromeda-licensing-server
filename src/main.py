from PyQt5.QtWidgets import QApplication
import sys
from PyQt5.QtGui import QIcon

# from core.constants import __VERSION__, ICON_PATH
from main_controller import AndromedaLicenseWindow

ICON_PATH = "src/gui/icons/logo.svg"


def main():
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon(ICON_PATH))
    app.setApplicationName("Andromeda")
    app.setOrganizationName("GIECAR / PRIO")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")

    controller = AndromedaLicenseWindow()
    controller.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
