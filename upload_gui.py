import sys
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets

import gui


def main():
    """
    Entry point for GUI
    :return:
    """
    app = QtWidgets.QApplication(["IRIDA Uploader"])
    dlg = gui.MainDialog()
    dlg.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
