import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui

from iridauploader.api import UPLOAD_MODES
from iridauploader.config import config
from iridauploader.model import DirectoryStatus

from iridauploader.gui.config import ConfigDialog
from iridauploader.gui import tools, widgets, colours, threads

import os


class MainDialog(QtWidgets.QDialog):
    """
    The programs main interactive window.

    Includes directory selection, automatic parsing, sample/project preview and error reporting.

    The user will be warned when a run is invalid, has already been uploaded, or errors happen during upload.
    """
    def __init__(self):
        super().__init__()
        logging.debug("GUI: Setting up MainDialog")

        self.config_dlg = ConfigDialog(parent=self)

        # set window title and icon
        self.setWindowTitle("IRIDA Uploader")
        icon_path = os.path.join(os.path.dirname(__file__), 'images/icon.ico')
        self.setWindowIcon(QtGui.QIcon(icon_path))

        # Initialize threads from the tools file
        self._status_thread = threads.StatusThread()
        self._parse_thread = threads.ParseThread()
        self._upload_thread = threads.UploadThread()

        # internal variables
        self._run_dir = ""
        self._config_file = ""
        self._uploading = False
        self._continue_partial = False

        # Setup gui objects
        self._init_objects()

        # Set Layout and Geometry
        self.setLayout(self._init_layout())
        # resize window
        self.setGeometry(0, 0, 800, 600)
        # Center Window
        qt_rectangle = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

        # Signals and Slots
        # buttons
        self._dir_button.clicked.connect(self._btn_open_dir)
        self._config_button.clicked.connect(self._btn_show_config)
        self._refresh_button.clicked.connect(self._btn_refresh)
        self._upload_button.clicked.connect(self._btn_upload)
        self._console_button.clicked.connect(self._btn_log)
        self._info_btn.clicked.connect(self._btn_continue)
        self._info_partial_btn.clicked.connect(self._btn_continue_partial)
        # connect threads finishing to finish functions
        self._status_thread.finished.connect(self._thread_finished_status)
        self._parse_thread.finished.connect(self._thread_finished_parse)
        self._upload_thread.finished.connect(self._thread_finished_upload)

        # init the config file
        config.setup()
        # block uploading at start
        self._upload_button.set_block()

    def _init_objects(self):
        """
        Setup all the objects that appear in the program
        :return: None
        """
        # directory
        self._dir_button = QtWidgets.QPushButton(self)
        self._dir_button.setText("Open Run Directory")
        self._dir_button.setFixedWidth(200)
        self._dir_line = QtWidgets.QLineEdit(self)
        self._dir_line.setReadOnly(True)
        self._dir_line.setEnabled(False)
        self._dir_line.setStyleSheet("color: black")
        # config
        self._config_button = QtWidgets.QPushButton(self)
        self._config_button.setText("Configure Settings")
        self._config_button.setFixedWidth(200)
        # refresh
        self._refresh_button = QtWidgets.QPushButton(self)
        self._refresh_button.setText("Refresh")
        # upload mode
        self._upload_mode_label = QtWidgets.QLabel("Upload Mode: ")
        self._upload_mode_combobox = QtWidgets.QComboBox(self)
        self._upload_mode_combobox.addItems(UPLOAD_MODES)
        self._upload_mode_combobox.setCurrentIndex(0)
        # Info lines, these start out as hidden
        self._info_line = QtWidgets.QLineEdit(self)
        self._info_line.setReadOnly(True)
        self._info_line.setStyleSheet("background-color: {}".format(colours.YELLOW_LIGHT))
        self._info_line.hide()
        self._prev_errors = QtWidgets.QPlainTextEdit(self)
        self._prev_errors.setReadOnly(True)
        self._prev_errors.hide()
        self._info_btn = QtWidgets.QPushButton(self)
        self._info_btn.setText("Continue")
        self._info_btn.setStyleSheet("background-color: {}".format(colours.RED_LIGHT))
        self._info_btn.hide()
        self._info_partial_btn = QtWidgets.QPushButton(self)
        self._info_partial_btn.setText("Continue Partially Uploaded Run")
        self._info_partial_btn.setStyleSheet("background-color: {}".format(colours.BLUE_LIGHT))
        self._info_partial_btn.hide()
        self._curr_errors = QtWidgets.QPlainTextEdit(self)
        self._curr_errors.setReadOnly(True)
        self._curr_errors.setStyleSheet("background-color: {}".format(colours.RED_LIGHT))
        self._curr_errors.hide()
        # Upload button
        self._upload_button = widgets.UploadButton(self)
        # Table
        self._table = widgets.SampleTable(self)
        # Upload error text
        self._upload_errors = QtWidgets.QPlainTextEdit(self)
        self._upload_errors.setReadOnly(True)
        self._upload_errors.setStyleSheet("background-color: {}".format(colours.RED_LIGHT))
        self._upload_errors.hide()
        # Logging console
        self._console = widgets.LogTextBox(self)
        self._console_button = QtWidgets.QPushButton(self)
        self._console_button.setFixedWidth(100)
        self._console_button.setText("Show Log")

    def _init_layout(self):
        """
        Setup layout
        :return: QtWidgets.QVBoxLayout
        """
        # main layout
        layout = QtWidgets.QVBoxLayout()

        # Directory selection
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.addWidget(self._dir_button)
        dir_layout.addWidget(self._dir_line)
        layout.addLayout(dir_layout)

        # Config selection & upload mode & refresh
        config_layout = QtWidgets.QHBoxLayout()
        config_layout.addWidget(self._config_button)
        upload_mode_layout = QtWidgets.QHBoxLayout()
        upload_mode_layout.addWidget(self._upload_mode_label)
        upload_mode_layout.addWidget(self._upload_mode_combobox)
        config_layout.addLayout(upload_mode_layout)
        config_layout.addWidget(self._refresh_button)
        layout.addLayout(config_layout)

        # info
        layout.addWidget(self._info_line)
        layout.addWidget(self._prev_errors)
        info_btn_layout = QtWidgets.QHBoxLayout()
        info_btn_layout.addWidget(self._info_btn)
        info_btn_layout.addWidget(self._info_partial_btn)
        layout.addLayout(info_btn_layout)
        layout.addWidget(self._curr_errors)

        # table
        layout.addWidget(self._table)

        # Upload error
        layout.addWidget(self._upload_errors)

        # Upload button
        upload_layout = QtWidgets.QHBoxLayout()
        upload_layout.addWidget(self._upload_button)
        upload_layout.addWidget(self._console_button)
        layout.addLayout(upload_layout)

        # logging text box
        layout.addWidget(self._console)

        return layout

    def closeEvent(self, event):
        """
        Override closeEvent to give warning before closing the application.

        If uploads are currently running, user will prompted before exiting the program
        :param event:
        :return:
        """
        if self._uploading:
            reply = QtWidgets.QMessageBox.question(self, 'Exit Uploader?',
                                                   "Data is still being uploaded! "
                                                   "Are you sure you want to exit the program?",
                                                   QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    #################
    #    Buttons    #
    #################

    def _btn_open_dir(self):
        """
        Opens a file(directory) dialog and sets the _run_dir variable to chosen directory
        Updates ui to reflect changes
        :return:
        """
        logging.debug("GUI: _btn_open_dir clicked")
        self._run_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self._dir_line.setText(self._run_dir)
        logging.debug("GUI: result: " + self._run_dir)

        # Kick of status check and parsing after opening a new directory
        self._start_status()

    def _btn_show_config(self):
        """
        Open the config dialog window
        After the dialog closes, contacts irida again (which updates the gui element)
        :return:
        """
        self.config_dlg.center_window()
        self.config_dlg.exec()

        # restart the status thread
        self._start_status()

    def _btn_refresh(self):
        """
        Clicking the refresh button re-tries the connection to IRIDA, and then re-tries a parse
        :return:
        """
        # restart the status thread
        self._start_status()

    def _btn_upload(self):
        """
        Blocks usage of the ui elements, and starts the upload thread with the set variables
        :return:
        """
        logging.debug("GUI: _btn_upload clicked")

        if tools.is_connected_to_irida():
            self._start_upload()
        else:
            # If no connection to irida, display a warning to the user
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("Cannot Connect to IRIDA")
            msg.setInformativeText('Please check your configuration')
            msg.setWindowTitle("Connection Error")
            # You need 2 buttons on the widget for the exit button to not be the same as the Open Config button
            # So we add an "OK" button, and then hide it
            p_config_button = msg.addButton("Open Config", QtWidgets.QMessageBox.YesRole)
            p_accept_button = msg.addButton("OK", QtWidgets.QMessageBox.NoRole)
            p_accept_button.hide()
            # Show the window, and don't let user interact with main dialog
            msg.exec()
            # allow user to go directoy to the config page
            if msg.clickedButton() == p_config_button:
                self._btn_show_config()

    def _btn_log(self):
        """
        If the log is hidden, show, and vice versa
        :return:
        """
        if self._console.isVisible():
            self._console.hide()
            self._console_button.setText("Show Log")
        else:
            self._console.show()
            self._console_button.setText("Hide Log")

    def _btn_continue(self, continue_partial=False):
        """
        Reset the error gui elements, and continue onto the parse phase
        By default does not use continue_partial flag
        :return:
        """
        self._continue_partial = continue_partial
        self._reset_previous_error()
        self._reset_info_line()
        self._start_parse()

    def _btn_continue_partial(self):
        """
        Continues the upload with the continue_partial flag enabled
        :return:
        """
        self._btn_continue(continue_partial=True)

    #######################
    #   Thread Starters   #
    #######################

    def _start_status(self):
        """
        Blocks usage of the ui elements
        Clear data and info out of gui
        Starts the status thread
        This acts as the logical start point for status/parsing run directories
        :return:
        """
        logging.debug("GUI: _btn_upload clicked")

        # lock the gui so users don't click things while the parsing is still happening.
        self._lock_gui()
        # Clear everything
        self._table.clear_table()
        self._reset_info_line()
        self._reset_previous_error()
        self._reset_current_error()
        self._reset_upload_error()

        # start status thread
        self._status_thread.set_vars(self._run_dir)
        self._status_thread.start()

    def _start_parse(self):
        """
        Starts the parse thread
        :return:
        """
        logging.debug("GUI: _start_parse clicked")
        # lock gui
        self._lock_gui()
        # start parsing
        self._parse_thread.set_vars(self._run_dir, self._continue_partial)
        self._parse_thread.start()

    def _start_upload(self):
        # Lock Gui
        self._lock_gui()
        self._upload_button.set_uploading()
        self._uploading = True
        # start upload
        upload_mode = self._upload_mode_combobox.currentText()
        self._upload_thread.set_vars(
            run_dir=self._run_dir, upload_mode=upload_mode, partial_continue=self._continue_partial)
        self._upload_thread.start()

    ##########################
    #    Threads Complete    #
    ##########################

    def _thread_finished_status(self):
        """
        Main logic for post status

        unlock gui (blocked when thread started)

        On invalid runs:
            show user error
            don't let user continue past error to parsing
            block uploading (no continue allowed)
        On New runs:
            start parsing run directory
        On Complete / Partial / Delayed / Error runs:
            Show user the state (complete, partial, delayed, error) and the reason for the state (error msg)
            Allow users to click continue to continue on to parsing the run
            Block uploading (until continue is clicked)

        :return: None
        """
        logging.debug("GUI: _thread_finished_status called")

        self._continue_partial = False

        # since the thread finished, we need to unlock the gui
        self._unlock_gui()

        status = self._status_thread.get_result()

        if status.status_equals(DirectoryStatus.INVALID):
            # Then we need to block upload, since it's invalid
            self._upload_button.set_block()
            # Give info in info line
            self._show_and_fill_info_line("Run is not valid: " + str(status.message))
            # an invalid run cannot be continued
            self._hide_info_button()

        elif status.status_equals(DirectoryStatus.NEW):
            # new runs start the parse immediately
            self._start_parse()

        elif status.status_equals(DirectoryStatus.COMPLETE):
            # We need to block upload until the user clicks continue
            self._upload_button.set_block()
            # give user info
            self._show_and_fill_info_line("This run directory has already been uploaded. "
                                          "Click 'Continue' if you want to proceed anyway.")

        elif status.status_equals(DirectoryStatus.DELAYED):
            # We need to block upload until the user clicks continue
            self._upload_button.set_block()
            # give user info
            self._show_and_fill_info_line("This run directory has been given a delay. "
                                          "Click 'Continue' if you want to proceed anyway.")

        elif status.status_equals(DirectoryStatus.PARTIAL):
            # We need to block upload until the user clicks continue
            self._upload_button.set_block()
            # give user info
            self._show_and_fill_info_partial_upload_options(
                "This run directory is partially uploaded. Choose how you would like to Continue.")

        elif status.status_equals(DirectoryStatus.ERROR):
            # We need to block upload until the user clicks continue
            self._upload_button.set_block()
            # give user info
            self._show_and_fill_info_line("This run directory previously had the error(s) below. "
                                          "Click 'Continue' if you want to proceed anyway.")
            self._show_previous_error(status.message)

    def _thread_finished_parse(self):
        """
        Checks if run was parsed correctly or not,
        fills table is valid
        shows users error and blocks upload if run did not parse
        Unblocks the UI elements
        :return:
        """
        logging.debug("GUI: _thread_finished_parse called")

        # get data from the thread object
        sequencing_run = self._parse_thread.get_run()

        if sequencing_run:
            # run parsed correctly
            self._table.fill_table(sequencing_run, self._continue_partial)
            self._unlock_gui()
        else:
            run_errors = self._parse_thread.get_error()
            self._show_current_error(run_errors)
            self._unlock_gui()
            # block uploading runs with parsing errors
            self._upload_button.set_block()

    def _thread_finished_upload(self):
        """
        Unblocks the UI elements,
        :return:
        """
        self._uploading = False
        self._continue_partial = False

        logging.debug("GUI: _thread_finished_upload called")
        if not self._upload_thread.is_success():
            error = self._upload_thread.get_exit_error()
            self._show_upload_error(str(error))
            # Unlock GUI
            self._unlock_gui()
            self._upload_button.set_block()
        else:
            # Unlock GUI
            self._unlock_gui()
            self._upload_button.set_finished()

    ############################
    #   Show/Hide/Fill/Clear   #
    ############################

    def _show_and_fill_info_line(self, message):
        """
        shows the info line
        fills the info line with message
        shows the info button (continue button)
        :param message: string to display to the user
        :return:
        """
        self._info_line.setText(message)
        self._info_line.show()
        self._info_btn.show()

    def _show_and_fill_info_partial_upload_options(self, message):
        """
        When it is a partial run, show info line with multiple options

        :param message: string to display to the user
        :return:
        """
        self._info_line.setText(message)
        self._info_line.show()
        self._info_btn.setText("Restart Run From Beginning")
        self._info_btn.show()
        self._info_partial_btn.show()

    def _reset_info_line(self):
        """
        Hides the info line
        blanks out the info line
        :return:
        """
        self._info_line.setText("")
        self._info_line.hide()
        self._info_btn.setText("Continue")
        self._info_btn.hide()
        self._info_partial_btn.hide()

    def _hide_info_button(self):
        """
        disables the use of the info (continue) button
        Useful in the case of an invalid run that should never be parsed
        :return:
        """
        self._info_btn.hide()
        self._info_partial_btn.hide()

    def _show_previous_error(self, errors):
        """
        Shows errors from a previous run attempt
        unhides a textbox and fills it with a string
        :param errors: string of errors to display to user
        :return:
        """
        self._prev_errors.show()
        self._prev_errors.appendPlainText(str(errors))

    def _reset_previous_error(self):
        """
        blanks out and hides the previous error box
        :return:
        """
        self._prev_errors.clear()
        self._prev_errors.hide()

    def _show_current_error(self, errors):
        """
        Shows errors from a current parse attempt
        unhides a textbox and fills it with a string
        :param errors: string of errors to display to user
        :return:
        """
        self._curr_errors.show()
        self._curr_errors.appendPlainText(str(errors))

    def _reset_current_error(self):
        """
        blanks out and hides the current error box
        :return:
        """
        self._curr_errors.clear()
        self._curr_errors.hide()

    def _show_upload_error(self, errors):
        """
        Shows errors from a current upload
        unhides a textbox and fills it with a string
        :param errors: string of errors to display to user
        :return:
        """
        self._upload_errors.show()
        self._upload_errors.appendPlainText(str(errors))

    def _reset_upload_error(self):
        """
        blanks out and hides the current upload error box
        :return:
        """
        self._upload_errors.clear()
        self._upload_errors.hide()

    def _lock_gui(self):
        """
        Locks gui elements that users should not be able to interact with when threads are running
        :return:
        """
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)
        self._refresh_button.setEnabled(False)
        self._upload_button.set_block()

    def _unlock_gui(self):
        """
        Unlocks all the gui elements that are blocked for threading reasons
        :return:
        """
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)
        self._refresh_button.setEnabled(True)

        # Check that we have a connection to IRIDA, if there is no connection, block upload to prevent errors
        self._upload_button.set_ready()
