import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore

from core import logger
from config import config
from progress import signal_worker
from model import DirectoryStatus

from .config import ConfigDialog
from .tools import StatusThread, ParseThread, UploadThread, QtHandler


class MainDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        logging.debug("GUI: Setting up MainDialog")

        self.config_dlg = ConfigDialog(parent=self)

        # Initialize threads
        # todo
        self._status_thread = StatusThread()
        self._parse_thread = ParseThread()
        self._upload_thread = UploadThread()

        # internal variables
        self._run_dir = ""
        self._force_state = False
        self._config_file = ""

        ###################################
        #           QT Objects            #
        ###################################

        # directory
        self._dir_button = QtWidgets.QPushButton(self)
        self._dir_button.setText("Open Run Directory")
        self._dir_line = QtWidgets.QLineEdit(self)
        self._dir_line.setReadOnly(True)
        # config
        self._config_button = QtWidgets.QPushButton(self)
        self._config_button.setText("Configure Settings")
        # refresh
        self._refresh_button = QtWidgets.QPushButton(self)
        self._refresh_button.setText("Refresh")
        # upload
        self._upload_button = QtWidgets.QPushButton(self)
        self._upload_button.setText('Start Upload')
        # Upload Progress
        self._current_project_label = QtWidgets.QLabel("Current Project:")
        self._current_project = QtWidgets.QLineEdit()
        self._current_project.setReadOnly(True)
        self._project_progress_label = QtWidgets.QLabel("Project Upload Progress")
        self._project_progress = QtWidgets.QProgressBar()
        self._current_sample_label = QtWidgets.QLabel("Current Sample:")
        self._current_sample = QtWidgets.QLineEdit()
        self._current_sample.setReadOnly(True)
        self._sample_progress_label = QtWidgets.QLabel("Sample Upload Progress")
        self._sample_progress = QtWidgets.QProgressBar()
        self._current_file_label = QtWidgets.QLabel("Current File:")
        self._current_file = QtWidgets.QLineEdit()
        self._current_file.setReadOnly(True)
        self._file_progress_label = QtWidgets.QLabel("File Upload Progress")
        self._file_progress = QtWidgets.QProgressBar()

        # todo
        # Table
        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Sample Name", "File 1", "File 2", "Project"])

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
        # connect threads finishing to finish functions
        self._status_thread.finished.connect(self.finished_status)
        self._parse_thread.finished.connect(self.finished_parse)
        self._upload_thread.finished.connect(self.finished_upload)
        # connect progress bars
        signal_worker.project_progress_signal.connect(self._project_progress.setValue)
        signal_worker.sample_progress_signal.connect(self._sample_progress.setValue)
        signal_worker.file_progress_signal.connect(self._file_progress.setValue)
        # connect current file/sample/project text boxes
        signal_worker.current_project_signal.connect(self.update_current_project)
        signal_worker.current_sample_signal.connect(self.update_current_sample)
        signal_worker.current_file_signal.connect(self.update_current_file)

        # init the config stuff
        config.setup()

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
        config_layout.addWidget(self._refresh_button)
        layout.addLayout(config_layout)

        # todo
        layout.addWidget(self._status_label)
        layout.addWidget(self._status_result)
        layout.addWidget(self._table)

        # Upload button
        layout.addWidget(self._upload_button)

        # Upload Progress
        current_project_layout = QtWidgets.QHBoxLayout()
        current_project_layout.addWidget(self._current_project_label)
        current_project_layout.addWidget(self._current_project)
        layout.addLayout(current_project_layout)
        project_progress_layout = QtWidgets.QHBoxLayout()
        project_progress_layout.addWidget(self._project_progress_label)
        project_progress_layout.addWidget(self._project_progress)
        layout.addLayout(project_progress_layout)

        current_sample_layout = QtWidgets.QHBoxLayout()
        current_sample_layout.addWidget(self._current_sample_label)
        current_sample_layout.addWidget(self._current_sample)
        layout.addLayout(current_sample_layout)
        sample_progress_layout = QtWidgets.QHBoxLayout()
        sample_progress_layout.addWidget(self._sample_progress_label)
        sample_progress_layout.addWidget(self._sample_progress)
        layout.addLayout(sample_progress_layout)

        current_file_layout = QtWidgets.QHBoxLayout()
        current_file_layout.addWidget(self._current_file_label)
        current_file_layout.addWidget(self._current_file)
        layout.addLayout(current_file_layout)
        file_progress_layout = QtWidgets.QHBoxLayout()
        file_progress_layout.addWidget(self._file_progress_label)
        file_progress_layout.addWidget(self._file_progress)
        layout.addLayout(file_progress_layout)

        # todo make collapsible
        # logging text box
        layout.addWidget(self._console)

        return layout

    def write_log_and_redraw(self, text):
        """
        Adds the text given to the logger box, and repaints so it displays
        Used as a slot for emits
        :param text:
        :return:
        """
        self._console.appendPlainText(text)
        self._console.repaint()

    def update_current_project(self, text):
        """
        Set text and repaint
        Used as a slot for emits
        :param text:
        :return:
        """
        self._current_project.setText(text)
        self._current_project.repaint()

    def update_current_sample(self, text):
        """
        Set text and repaint
        Used as a slot for emits
        :param text:
        :return:
        """
        self._current_sample.setText(text)
        self._current_sample.repaint()

    def update_current_file(self, text):
        """
        Set text and repaint
        Used as a slot for emits
        :param text:
        :return:
        """
        self._current_file.setText(text)
        self._current_file.repaint()

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
        self.start_status_parse()

    def show_config(self):
        """
        Open the config dialog window
        :return:
        """
        self.config_dlg.center_window()
        self.config_dlg.show()

        # init / re-init config with config file selected
        # todo: This might be unnecessary,
        config.setup()

    # todo start
    def start_status_parse(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")

        # lock the gui so users don't click things while the parsing is still happening.
        self._lock_gui()

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
            print("gui status: invalid")
            # todo: do something with this info, tell the user is bad
            # since we return here, we need to unlock the gui
            self._unlock_gui()
            return
        elif status.status_equals(DirectoryStatus.NEW):
            print("gui status: new run")
            self._force_state = False
        elif status.status_equals(DirectoryStatus.COMPLETE):
            print("gui status: complete")
            # todo: warn users this was completed already & set force
            self._force_state = True
        elif status.status_equals(DirectoryStatus.PARTIAL):
            print("gui status: partial")
            # todo: warn users its partial & set force
            self._force_state = True
        elif status.status_equals(DirectoryStatus.ERROR):
            print("gui status: error")
            # todo: warn users that it was an error & set force
            self._force_state = True

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

        self._post_parse()

        # Unlock GUI
        self._unlock_gui()

    def _post_parse(self):
        sequencing_run = self._parse_thread.get_run()

        if sequencing_run:
            # run parsed correctly
            self._fill_table(sequencing_run)
        else:
            run_errors = self._parse_thread.get_error()
            # todo: do something when a run fails to parse

    # todo end

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
        # X index for the table
        SAMPLE_NAME = 0
        FILE_1 = 1
        FILE_2 = 2
        PROJECT = 3

        # total number of samples
        sample_count = 0

        project_list = sequencing_run.project_list
        for project in project_list:
            sample_list = project.sample_list
            sample_count = sample_count + len(sample_list)

        self._table.setRowCount(sample_count)

        y_index = 0
        for project in project_list:
            sample_list = project.sample_list
            for sample in sample_list:
                files = sample.sequence_file.file_list
                self._table.setItem(y_index, SAMPLE_NAME, QtWidgets.QTableWidgetItem(sample.sample_name))
                self._table.setItem(y_index, FILE_1, QtWidgets.QTableWidgetItem(files[0]))
                if len(files) == 2:
                    self._table.setItem(y_index, FILE_2, QtWidgets.QTableWidgetItem(files[1]))
                self._table.setItem(y_index, PROJECT, QtWidgets.QTableWidgetItem(project.id))

                y_index = y_index + 1

    def _lock_gui(self):
        # Lock Gui
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)

    def _unlock_gui(self):
        self._upload_button.setEnabled(True)
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)

