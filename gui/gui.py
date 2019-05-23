import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore

from core import logger
from config import config
from progress import signal_worker

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
        self._config_file = ""

        ###################################
        #           QT Objects            #
        ###################################

        # directory
        self._dir_label = QtWidgets.QLabel(self)
        self._dir_label.setText("Sequence Run Directory")
        self._dir_line = QtWidgets.QLineEdit(self)
        self._dir_line.setReadOnly(True)
        self._dir_button = QtWidgets.QPushButton(self)
        self._dir_button.setText("Open Directory")
        # config
        self._config_button = QtWidgets.QPushButton(self)
        self._config_button.setText("Configure Settings")
        # force upload
        self._force_checkbox = QtWidgets.QCheckBox(self)
        self._force_checkbox.setText("Force Upload")
        self._force_checkbox.setChecked(False)
        self._force_state = False
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
        self._table = QtWidgets.QTableWidget()
        self._table.setRowCount(10)
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Sample Name", "File 1", "File 2", "Project"])
        # self._table.
        self._status_result = QtWidgets.QLineEdit()
        self._status_result.setReadOnly(True)
        self._parse_button = QtWidgets.QPushButton()
        self._parse_button.setText("Parse Run")

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
        self._force_checkbox.stateChanged.connect(self.click_force_upload)
        self._upload_button.clicked.connect(self.start_upload)
        # connect threads finishing to finish functions
        # todo
        self._status_thread.finished.connect(self.finished_status)
        self._parse_button.clicked.connect(self.start_parse)
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

    def _layout(self):
        """
        Setup layout
        :return:
        """
        # main layout
        layout = QtWidgets.QVBoxLayout()

        # Directory selection
        dir_layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._dir_label)
        dir_layout.addWidget(self._dir_line)
        dir_layout.addWidget(self._dir_button)
        layout.addLayout(dir_layout)

        # Config selection & force checkbox & upload button
        config_layout = QtWidgets.QHBoxLayout()
        config_layout.addWidget(self._config_button)
        config_layout.addWidget(self._force_checkbox)
        config_layout.addWidget(self._upload_button)
        layout.addLayout(config_layout)

        # todo
        # Samples Table
        layout.addWidget(self._table)
        layout.addWidget(self._status_result)
        layout.addWidget(self._parse_button)

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

        # logging text box
        # todo
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
        # todo
        self.start_status()

    def show_config(self):
        """
        Open the config dialog window
        :return:
        """
        self.config_dlg.center_window()
        self.config_dlg.show()

    def click_force_upload(self, state):
        """
        Sets the _force_state variable to reflect the current checkbox state
        :param state: True/False
        :return:
        """
        logging.debug("GUI: click_force_upload clicked")
        if state == QtCore.Qt.Checked:
            logging.debug("GUI: set force upload to TRUE")
            self._force_state = True
        else:
            logging.debug("GUI: set force upload to False")
            self._force_state = False

    # todo start
    def start_status(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")
        # Lock Gui
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)
        self._force_checkbox.setEnabled(False)
        # init / re-init config with config file selected
        config.setup()
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

        if status.status == "new":
            print("new run")

        # Unlock GUI
        self._upload_button.setEnabled(True)
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)
        self._force_checkbox.setEnabled(True)

    def start_parse(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")
        # Lock Gui
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)
        self._force_checkbox.setEnabled(False)
        # init / re-init config with config file selected
        config.setup()
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
        # Output info
        print( str(self._parse_thread.get_run()))
        # Unlock GUI
        self._upload_button.setEnabled(True)
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)
        self._force_checkbox.setEnabled(True)
    # todo end

    def start_upload(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")
        # Lock Gui
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)
        self._force_checkbox.setEnabled(False)
        # init / re-init config with config file selected
        config.setup()
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
        self._upload_button.setEnabled(True)
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)
        self._force_checkbox.setEnabled(True)
        # reset checkbox
        self._force_state = False
        self._force_checkbox.setChecked(False)

    def _center_window(self):
        """
        Gets the windows size, and centers the main qt widget
        :return:
        """
        qt_rectangle = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())
