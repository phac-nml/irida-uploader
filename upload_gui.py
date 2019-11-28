import sys
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets

import gui

from appdirs import user_log_dir
import os
import traceback


def get_crash_log_file_path():
    # Normal base logging directory name
    log_directory_name = "irida_uploader"
    # Use systems default logging path, and append our named directory
    log_file_path = os.path.join(user_log_dir(log_directory_name), 'crash.log')
    # Create the directory if it doesn't exist
    if not os.path.exists(user_log_dir(log_directory_name)):
        os.makedirs(user_log_dir(log_directory_name))

    return log_file_path


def main():
    """
    Entry point for GUI
    :return:
    """
    try:
        app = QtWidgets.QApplication(["IRIDA Uploader"])
        dlg = gui.MainDialog()
        dlg.show()
        sys.exit(app.exec_())
    except Exception:
        # log full stack trace here
        traceback.print_exc(file=open(get_crash_log_file_path(), "a"))


if __name__ == '__main__':
    main()
