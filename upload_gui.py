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
    # When running tests, the Makefile creates an environment variable IRIDA_UPLOADER_TEST to 'True'
    # If it exists then we are running a test and should be logging to the test logs directory
    if os.environ.get('IRIDA_UPLOADER_TEST'):
        log_directory_name = "irida_uploader_test"
    # Use systems default logging path, and append our named directory
    log_file_path = os.path.join(user_log_dir(log_directory_name), 'crash.log')

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
