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

        # Initialize threads
        self._status_thread = StatusThread()
        self._parse_thread = ParseThread()
        self._upload_thread = UploadThread()

        # internal variables
        self._run_dir = ""
        self._force_state = False
        self._config_file = ""
        self._console_hidden = True
        self._table_sample_index_dict = None

        ###################################
        #           QT Objects            #
        ###################################

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
        # info
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
        self._curr_errors = QtWidgets.QPlainTextEdit(self)
        self._curr_errors.setReadOnly(True)
        self._curr_errors.setStyleSheet("background-color: pink")
        self._curr_errors.hide()

        self._info_btn.hide()
        # upload
        self._upload_button = QtWidgets.QPushButton(self)
        self._upload_button.setText('Start Upload')
        self._upload_button.setStyleSheet("background-color: lime")

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

        self._status_label = QtWidgets.QLabel("Status Result:")
        self._status_result = QtWidgets.QLineEdit()
        self._status_result.setReadOnly(True)

        # Setup logging handler
        handler = QtHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S'))
        handler.setLevel(logging.INFO)
        handler.message_writer.messageWritten.connect(self.write_log_and_redraw)
        logger.root_logger.addHandler(handler)
        self._console = QtWidgets.QPlainTextEdit(self)
        self._console.setReadOnly(True)
        self._console.hide()
        self._console_button = QtWidgets.QPushButton(self)
        self._console_button.setFixedWidth(100)
        self._console_button.setText("Show Log")

        # Set Layout and Geometry
        self.setLayout(self._layout())
        self.setGeometry(0, 0, 800, 600)
        # Center Window
        self._center_window()

        ######################################
        #         Signals and Slots          #
        ######################################

        # buttons
        self._dir_button.clicked.connect(self.open_dir)
        self._config_button.clicked.connect(self.show_config)
        self._refresh_button.clicked.connect(self.refresh)
        self._upload_button.clicked.connect(self.start_upload)
        self._console_button.clicked.connect(self.log_button_clicked)
        self._info_btn.clicked.connect(self.click_continue)
        # connect threads finishing to finish functions
        self._status_thread.finished.connect(self.finished_status)
        self._parse_thread.finished.connect(self.finished_parse)
        self._upload_thread.finished.connect(self.finished_upload)
        signal_worker.progress_signal.connect(self.update_progress)

        # init the config stuff
        config.setup()
        self.contact_irida()

    def _layout(self):
        """
        Setup layout
        :return:
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
        # config_layout.addWidget(self._status_label)
        # config_layout.addWidget(self._status_result)
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

        # todo make collapsible
        # logging text box
        layout.addWidget(self._console)

        return layout

    def update_progress(self, data):
        sample_name_project = data["sample"] + "." + str(data["project"])
        self._table_sample_index_dict[sample_name_project].setValue(data["progress"])

    def write_log_and_redraw(self, text):
        """
        Adds the text given to the logger box, and repaints so it displays
        Used as a slot for emits
        :param text:
        :return:
        """
        self._console.appendPlainText(text)
        self._console.repaint()

    def open_dir(self):
        """
        Opens a file(directory) dialog and sets the _run_dir variable to chosen directory
        Updates ui to reflect changes
        :return:
        """
        logging.debug("GUI: open_dir clicked")
        self._run_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self._dir_line.setText(self._run_dir)
        logging.debug("GUI: result: " + self._run_dir)

        # Kick of status check and parsing after opening a new directory
        self.start_status_parse()

    def refresh(self):
        self.contact_irida()
        self.start_status_parse()

    def show_config(self):
        """
        Open the config dialog window
        :return:
        """
        self.config_dlg.center_window()
        self.config_dlg.exec()

        # re-init connection
        self.contact_irida()

    def reset_info_line(self):
        self._info_line.setText("")
        self._info_line.hide()
        self._info_btn.hide()
        self._info_btn.setEnabled(True)

    def show_and_fill_info_line(self, message):
        self._info_line.setText(message)
        self._info_line.show()
        self._info_btn.show()

    def disable_info_button(self):
        self._info_btn.setEnabled(False)

    def show_previous_error(self, errors):
        self._prev_errors.show()
        self._prev_errors.appendPlainText(str(errors))

    def reset_previous_error(self):
        self._prev_errors.clear()
        self._prev_errors.hide()

    def show_current_error(self, errors):
        self._curr_errors.show()
        self._curr_errors.appendPlainText(str(errors))

    def reset_current_error(self):
        self._curr_errors.clear()
        self._curr_errors.hide()

    def log_button_clicked(self):
        if self._console_hidden:
            self._console.show()
            self._console_button.setText("Hide Log")
            self._console_hidden = False
        else:
            self._console.hide()
            self._console_button.setText("Show Log")
            self._console_hidden = True

    # todo start
    def start_status_parse(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")

        # lock the gui so users don't click things while the parsing is still happening.
        self._lock_gui()
        # Clear the table
        self._clear_table()
        # reset the info line
        self.reset_info_line()
        # reset error lines
        self.reset_previous_error()
        self.reset_current_error()

        # start upload
        self._status_thread.set_vars(self._run_dir)
        self._status_thread.start()

    def finished_status(self):
        """
        Unblocks the UI elements, resets the run directory and checkbox
        This acts as a slot for the upload thread on finish
        :return:
        """
        logging.debug("GUI: finished_upload called")
        # Output info
        status = self._status_thread.get_result()
        text = status.directory + ", " + status.status + ", " + str(status.message)
        self._status_result.setText(text)

        self.status_parse_logic(status)

    def status_parse_logic(self, status):

        if status.status_equals(DirectoryStatus.INVALID):
            # since we return here, we need to unlock the gui
            self._unlock_gui()
            # Then we need to block upload, since it's invalid
            self._block_upload()
            # Give info in info line
            self.show_and_fill_info_line("Run is not valid: " + str(status.message))
            # an invalid run cannot be continued
            self.disable_info_button()
            return
        elif status.status_equals(DirectoryStatus.NEW):
            self._force_state = False
            # new runs start the parse immediately
            self.start_parse()
        elif status.status_equals(DirectoryStatus.COMPLETE):
            # We need to block upload until the user clicks continue
            self._block_upload()
            # give user info
            self.show_and_fill_info_line("This run directory has already been uploaded. "
                                         "Click continue to proceed anyway.")
            # set force state for if user wants to continue anyways
            self._force_state = True
        elif status.status_equals(DirectoryStatus.PARTIAL):
            # We need to block upload until the user clicks continue
            self._block_upload()
            # give user info
            self.show_and_fill_info_line("This run directory may be partially uploaded. "
                                         "Click continue to proceed anyway.")
            # set force state for if user wants to continue anyways
            self._force_state = True
        elif status.status_equals(DirectoryStatus.ERROR):
            # We need to block upload until the user clicks continue
            self._block_upload()
            # give user info
            self.show_and_fill_info_line("This run directory previously had the error(s) below. "
                                         "Click continue to proceed anyway.")
            self.show_previous_error(status.message)
            # set force state for if user wants to continue anyways
            self._force_state = True

    def click_continue(self):
        self.reset_previous_error()
        self.reset_info_line()
        self.start_parse()

    def start_parse(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")
        # start upload
        self._parse_thread.set_vars(self._run_dir)
        self._parse_thread.start()

    def finished_parse(self):
        """
        Unblocks the UI elements, resets the run directory and checkbox
        This acts as a slot for the upload thread on finish
        :return:
        """
        logging.debug("GUI: finished_upload called")

        sequencing_run = self._parse_thread.get_run()

        if sequencing_run:
            # run parsed correctly
            self._fill_table(sequencing_run)
            self._unlock_gui()
        else:
            run_errors = self._parse_thread.get_error()
            self.show_current_error(run_errors)
            self._unlock_gui()
            # block uploading runs with parsing errors
            self._block_upload()

    def start_upload(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")
        # Lock Gui
        self._lock_gui()
        # start upload
        self._upload_thread.set_vars(self._run_dir, self._force_state)
        self._upload_thread.start()

    def finished_upload(self):
        """
        Unblocks the UI elements, resets the run directory and checkbox
        This acts as a slot for the upload thread on finish
        :return:
        """
        logging.debug("GUI: finished_upload called")
        # Unlock GUI
        self._unlock_gui()

    def _center_window(self):
        """
        Gets the windows size, and centers the main qt widget
        :return:
        """
        qt_rectangle = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

    def _fill_table(self, sequencing_run):
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
        self._table.clearContents()
        self._table.setRowCount(0)

    def _lock_gui(self):
        # Lock Gui
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)

    def _unlock_gui(self):
        self._upload_button.setEnabled(True)
        self._upload_button.setStyleSheet("background-color: lime")
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)

    def _block_upload(self):
        self._upload_button.setEnabled(False)
        self._upload_button.setStyleSheet("background-color: grey")

    def contact_irida(self):
        """
        Attempts to connect to IRIDA
        Sets the style and text of the status widget to green/red to indicate connected/error
        :return:
        """
        try:
            api_handler.initialize_api_from_config()
            self._connection_status.setText("Connection OK")
            self._connection_status.setStyleSheet("background-color: green; color: white;")
            logging.info("Successfully connected to IRIDA")
        except Exception:
            self._connection_status.setText("Connection Error")
            self._connection_status.setStyleSheet("background-color: red; color: white;")
            logging.info("Error occurred while trying to connect to IRIDA")
            self._block_upload()
