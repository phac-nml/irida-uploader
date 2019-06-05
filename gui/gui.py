import logging
import os
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets

from core import logger, api_handler
from config import config
from progress import signal_worker
from model import DirectoryStatus

from .config import ConfigDialog
from .tools import StatusThread, ParseThread, UploadThread, QtHandler

# X index for the table
TABLE_SAMPLE_NAME = 0
TABLE_FILE_1 = 1
TABLE_FILE_2 = 2
TABLE_PROJECT = 3
TABLE_PROGRESS = 4


class MainDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        logging.debug("GUI: Setting up MainDialog")

        self.config_dlg = ConfigDialog(parent=self)

        # Initialize threads from the tools file
        self._status_thread = StatusThread()
        self._parse_thread = ParseThread()
        self._upload_thread = UploadThread()

        # internal variables
        self._run_dir = ""
        self._force_state = False
        self._config_file = ""
        self._console_hidden = True
        self._table_sample_index_dict = None

        # Setup gui objects
        self._init_objects()

        # Setup logging handler
        handler = QtHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S'))
        handler.setLevel(logging.INFO)
        # connect to the log/redraw function
        handler.message_writer.messageWritten.connect(self._write_log_and_redraw)
        # finally add it to the logging module
        logger.root_logger.addHandler(handler)

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
        # connect threads finishing to finish functions
        self._status_thread.finished.connect(self._thread_finished_status)
        self._parse_thread.finished.connect(self._thread_finished_parse)
        self._upload_thread.finished.connect(self._thread_finished_upload)
        # connect progress module signals to updating progress function
        signal_worker.progress_signal.connect(self._signal_update_progress)

        # init the config file
        config.setup()
        # attempt connecting to IRIDA
        self._contact_irida()

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
        # config
        self._config_button = QtWidgets.QPushButton(self)
        self._config_button.setText("Configure Settings")
        self._config_button.setFixedWidth(200)
        # connection status
        self._connection_status = QtWidgets.QLineEdit(self)
        self._connection_status.setReadOnly(True)
        self._connection_status.setFixedWidth(300)
        # refresh
        self._refresh_button = QtWidgets.QPushButton(self)
        self._refresh_button.setText("Refresh")
        # Info lines, these start out as hidden
        self._info_line = QtWidgets.QLineEdit(self)
        self._info_line.setReadOnly(True)
        self._info_line.setStyleSheet("background-color: yellow")
        self._info_line.hide()
        self._prev_errors = QtWidgets.QPlainTextEdit(self)
        self._prev_errors.setReadOnly(True)
        self._prev_errors.hide()
        self._info_btn = QtWidgets.QPushButton(self)
        self._info_btn.setText("!!! Continue !!!")
        self._info_btn.setStyleSheet("background-color: red")
        self._info_btn.hide()
        self._curr_errors = QtWidgets.QPlainTextEdit(self)
        self._curr_errors.setReadOnly(True)
        self._curr_errors.setStyleSheet("background-color: pink")
        self._curr_errors.hide()
        # Upload button
        self._upload_button = QtWidgets.QPushButton(self)
        self._upload_button.setText('Start Upload')
        self._upload_button.setStyleSheet("background-color: lime; color: black")
        # Table
        self._table = QtWidgets.QTableWidget()
        self._table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Sample Name", "File 1", "File 2", "Project", "Progress"])
        self._table.setColumnWidth(TABLE_SAMPLE_NAME, 170)
        self._table.setColumnWidth(TABLE_FILE_1, 200)
        self._table.setColumnWidth(TABLE_FILE_2, 200)
        self._table.setColumnWidth(TABLE_PROJECT, 70)
        self._table.setColumnWidth(TABLE_PROGRESS, 135)
        # Logging console
        self._console = QtWidgets.QPlainTextEdit(self)
        self._console.setReadOnly(True)
        self._console.hide()
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

        # Config selection & refresh
        config_layout = QtWidgets.QHBoxLayout()
        config_layout.addWidget(self._config_button)
        config_layout.addWidget(self._connection_status)
        config_layout.addWidget(self._refresh_button)
        layout.addLayout(config_layout)

        # info
        layout.addWidget(self._info_line)
        layout.addWidget(self._prev_errors)
        layout.addWidget(self._info_btn)
        layout.addWidget(self._curr_errors)

        # table
        layout.addWidget(self._table)

        # Upload button
        upload_layout = QtWidgets.QHBoxLayout()
        upload_layout.addWidget(self._upload_button)
        upload_layout.addWidget(self._console_button)
        layout.addLayout(upload_layout)

        # logging text box
        layout.addWidget(self._console)

        return layout

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

        # re-init connection
        self._contact_irida()
        # redo the status thread for safety
        self._start_status()

    def _btn_refresh(self):
        """
        Clicking the refresh button re-tries the connection to IRIDA, and then re-tries a parse
        :return:
        """
        # try connecting to IRIDA again
        self._contact_irida()
        # kick off status thread
        self._start_status()

    def _btn_upload(self):
        """
        Blocks usage of the ui elements, and starts the upload thread with the set variables
        :return:
        """
        logging.debug("GUI: _btn_upload clicked")
        # Lock Gui
        self._lock_gui()
        # start upload
        self._upload_thread.set_vars(self._run_dir, self._force_state)
        self._upload_thread.start()

    def _btn_log(self):
        """
        If the log is hidden, show, and vice versa
        :return:
        """
        if self._console_hidden:
            self._console.show()
            self._console_button.setText("Hide Log")
            self._console_hidden = False
        else:
            self._console.hide()
            self._console_button.setText("Show Log")
            self._console_hidden = True

    def _btn_continue(self):
        """
        Reset the error gui elements, and continue onto the parse phase
        :return:
        """
        self._reset_previous_error()
        self._reset_info_line()
        self._start_parse()

    #################
    #    Threads    #
    #################

    def _thread_finished_status(self):
        """
        Main logic for post status

        unlock gui (blocked when thread started)

        On invalid runs:
            show user error
            don't let user continue past error to parsing
            block uploading (no continue allowed)
        On New runs:
            set force state to false (run is clean, no force needed)
            start parsing run directory
        On Complete / Partial / Error runss:
            set force stat to True (run is not clean, force is needed if we end up proceeding
            Show user the state (complete, partial, error) and the reason for the state (error msg)
            Allow users to click continue to continue on to parsing the run
            Block uploading (until continue is clicked)

        :return: None
        """
        logging.debug("GUI: _thread_finished_status called")

        # since the thread finished, we need to unlock the gui
        self._unlock_gui()

        status = self._status_thread.get_result()

        if status.status_equals(DirectoryStatus.INVALID):
            # Then we need to block upload, since it's invalid
            self._block_upload()
            # Give info in info line
            self._show_and_fill_info_line("Run is not valid: " + str(status.message))
            # an invalid run cannot be continued
            self._disable_info_button()

        elif status.status_equals(DirectoryStatus.NEW):
            self._force_state = False
            # new runs start the parse immediately
            self._start_parse()

        elif status.status_equals(DirectoryStatus.COMPLETE):
            # We need to block upload until the user clicks continue
            self._block_upload()
            # give user info
            self._show_and_fill_info_line("This run directory has already been uploaded. "
                                         "Click continue to proceed anyway.")
            # set force state for if user wants to continue anyways
            self._force_state = True

        elif status.status_equals(DirectoryStatus.PARTIAL):
            # We need to block upload until the user clicks continue
            self._block_upload()
            # give user info
            self._show_and_fill_info_line("This run directory may be partially uploaded. "
                                         "Click continue to proceed anyway.")
            # set force state for if user wants to continue anyways
            self._force_state = True

        elif status.status_equals(DirectoryStatus.ERROR):
            # We need to block upload until the user clicks continue
            self._block_upload()
            # give user info
            self._show_and_fill_info_line("This run directory previously had the error(s) below. "
                                         "Click continue to proceed anyway.")
            self._show_previous_error(status.message)
            # set force state for if user wants to continue anyways
            self._force_state = True

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
            self._fill_table(sequencing_run)
            self._unlock_gui()
        else:
            run_errors = self._parse_thread.get_error()
            self._show_current_error(run_errors)
            self._unlock_gui()
            # block uploading runs with parsing errors
            self._block_upload()

    def _thread_finished_upload(self):
        """
        Unblocks the UI elements,
        :return:
        """
        logging.debug("GUI: _thread_finished_upload called")
        # TODO Add upload error logic here (like parse logic above)
        # Unlock GUI
        self._unlock_gui()
        self._block_upload_finished_success()

    def _signal_update_progress(self, data):
        """
        concatenates sample name and project id into key for table, then updates progress bar
        :param data:
        :return:
        """
        sample_name_project = data["sample"] + "." + str(data["project"])
        self._table_sample_index_dict[sample_name_project].setValue(data["progress"])

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
        self._clear_table()
        self._reset_info_line()
        self._reset_previous_error()
        self._reset_current_error()

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
        self._parse_thread.set_vars(self._run_dir)
        self._parse_thread.start()

    ############################
    #   Show/Hide/Fill/Clear   #
    ############################

    def _contact_irida(self):
        """
        Attempts to connect to IRIDA
        Sets the style and text of the status widget to green/red to indicate connected/error
        :return:
        """
        try:
            api_handler.initialize_api_from_config()
            self._connection_status.setText("Connection OK")
            self._connection_status.setStyleSheet("background-color: green; color: white;")
            logging.info("GUI: Successfully connected to IRIDA")
        # todo: advanced error handling from the api side would be nice (tell users what part failed)
        except Exception:
            self._connection_status.setText("Connection Error")
            self._connection_status.setStyleSheet("background-color: red; color: white;")
            logging.info("GUI: Error occurred while trying to connect to IRIDA")
            self._block_upload()

    def _write_log_and_redraw(self, text):
        """
        Adds the text given to the logger box, and repaints so it displays
        Used as a slot for emits
        :param text:
        :return:
        """
        self._console.appendPlainText(text)
        self._console.repaint()

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

    def _reset_info_line(self):
        """
        Hides the info line
        blanks out the info line
        unblocks the info button
        :return: 
        """
        self._info_line.setText("")
        self._info_line.hide()
        self._info_btn.hide()
        self._info_btn.setEnabled(True)

    def _disable_info_button(self):
        """
        disables the use of the info (continue) button
        Useful in the case of an invalid run that should never be parsed
        :return: 
        """
        self._info_btn.setEnabled(False)

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

    def _fill_table(self, sequencing_run):
        """
        Given a SequencingRun, fill the table with data
        includes sample name, file names, project, and progress widget
        :param sequencing_run: SequencingRun object
        :return:
        """
        # total number of samples
        sample_count = 0

        project_list = sequencing_run.project_list
        for project in project_list:
            sample_list = project.sample_list
            sample_count = sample_count + len(sample_list)

        self._table.setRowCount(sample_count)
        self._table_sample_index_dict = {}

        y_index = 0
        for project in project_list:
            sample_list = project.sample_list
            for sample in sample_list:
                files = sample.sequence_file.file_list
                self._table.setItem(y_index, TABLE_SAMPLE_NAME, QtWidgets.QTableWidgetItem(sample.sample_name))
                self._table.setItem(y_index, TABLE_FILE_1, QtWidgets.QTableWidgetItem(os.path.basename(files[0])))
                if len(files) == 2:
                    self._table.setItem(y_index, TABLE_FILE_2, QtWidgets.QTableWidgetItem(os.path.basename(files[1])))
                self._table.setItem(y_index, TABLE_PROJECT, QtWidgets.QTableWidgetItem(project.id))

                new_progress_bar = QtWidgets.QProgressBar()
                self._table.setCellWidget(y_index, TABLE_PROGRESS, new_progress_bar)
                sample_project_key = sample.sample_name + "." + str(project.id)
                self._table_sample_index_dict[sample_project_key] = new_progress_bar

                y_index = y_index + 1

    def _clear_table(self):
        """
        Wipes out tables contents and sets the row count back to 0
        :return:
        """
        self._table.clearContents()
        self._table.setRowCount(0)

    def _lock_gui(self):
        """
        Locks gui elements that users should not be able to interact with when threads are running
        :return:
        """
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)

    def _unlock_gui(self):
        """
        Unlocks all the gui elements that are blocked for threading reasons
        :return:
        """
        self._upload_button.setEnabled(True)
        self._upload_button.setText("Upload")
        self._upload_button.setStyleSheet("background-color: lime; color: black")
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)

    def _block_upload(self):
        """
        blocks the upload button, so that invalid/errorred runs cannot be run
        :return:
        """
        self._upload_button.setEnabled(False)
        self._upload_button.setText("Upload")
        self._upload_button.setStyleSheet("background-color: grey; color: white")

    def _block_upload_finished_success(self):
        """
        blocks the upload button, so that invalid/error runs cannot be run
        :return:
        """
        self._upload_button.setEnabled(False)
        self._upload_button.setText("Complete")
        self._upload_button.setStyleSheet("background-color: aqua; color: black")
