import sys
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets

from appdirs import user_log_dir
import os
import traceback

import iridauploader.gui.main_dialog as main_dialog


def get_crash_log_file_path():
    # Normal base logging directory name
    log_directory_name = "irida-uploader"
    # Use systems default logging path, and append our named directory
    log_file_path = os.path.join(user_log_dir(log_directory_name), 'crash.log')
    # Create the directory if it doesn't exist
    if not os.path.exists(user_log_dir(log_directory_name)):
        os.makedirs(user_log_dir(log_directory_name))

    return log_file_path


def except_hook(error_exctype, error_value, error_traceback):
    # This function is used to override the default __excepthook__ so that we can write our crash log to file

    # keep existing functionality of __excepthook__
    sys.__excepthook__(error_exctype, error_value, error_traceback)

    # get a formatted string with out traceback and print it to our crash log file
    tb = ''.join(traceback.format_tb(error_traceback))
    f = open(get_crash_log_file_path(), "a+")
    f.write(tb)

    # after an exception like this, exit with error
    sys.exit(1)


def main():
    """
    Entry point for GUI
    :return:
    """
    app = QtWidgets.QApplication(["IRIDA Uploader"])
    dlg = main_dialog.MainDialog()
    dlg.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    # override except hook for custom crash log
    sys.excepthook = except_hook
    main()
