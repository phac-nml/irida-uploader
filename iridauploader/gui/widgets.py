# This file contains custom widgets used by the main and config dialog windows

import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets

import os

from iridauploader.core import logger
import iridauploader.progress as progress

from . import colours, tools


class ProgressBarHandler:
    """
    This class handles a dictionary of progress bars, indexed off of the project/sample list in the sequencing run
    It simplifies updating the progress bars percentage by allowing us to pass it only the sample and project to update
    """
    def __init__(self, q_parent=None):
        # Create a dictionary for new progress bars
        self._bar_dict = {}
        # link the qt parent so things die correctly
        self._q_parent = q_parent

    @staticmethod
    def _get_key(sample, project):
        """
        Key is created by joining the sample and project id together with a period
        :param sample:
        :param project:
        :return:
        """
        return sample + "." + project

    def _get_bar(self, sample, project):
        """
        Gets the progress bars key and returns is
        :param sample:
        :param project:
        :return:
        """
        return self._bar_dict[self._get_key(sample, project)]

    def add_bar(self, sample, project):
        """
        Create a new progress bar given a sample and project id
        :param sample: sample name
        :param project: project id
        :return: QUploadProgressBar
        """
        key = self._get_key(sample, project)
        bar = self.QUploadProgressBar(parent=self._q_parent)
        self._bar_dict[key] = bar
        return bar

    def clear(self):
        """
        Clears all the progress bars
        :return:
        """
        self._bar_dict.clear()

    def set_value(self, sample, project, value):
        """
        Sets the value of a progress bar given a sample and project id
        :param sample: sample name
        :param project: project id
        :param value: value to set (0-100), if the sample is paired end, the progress advances at half rate
        :return:
        """
        bar = self._get_bar(sample, project)
        bar.setValue(value)

    class QUploadProgressBar(QtWidgets.QProgressBar):
        # Styles for progress bar using the Qt style sheet format
        DEFAULT_STYLE = (
            "QProgressBar{{text-align: center}}"
            "QProgressBar::chunk {{background-color: {0}; width: 10px; margin: 0px;}}".format(
                colours.BLUE_LIGHT
            )
        )
        COMPLETED_STYLE = (
            "QProgressBar{{text-align: center}}"
            "QProgressBar::chunk {{background-color: {}; width: 10px; margin: 0px;}}".format(
                colours.GREEN_LIGHT
            )
        )

        def __init__(self, parent=None):
            super().__init__()
            QtWidgets.QProgressBar.__init__(self, parent)
            self.setStyleSheet(self.DEFAULT_STYLE)

        def setValue(self, value):
            """
            Sets the value of of the progress bar
            :param value: int or float
            :return: None
            """
            QtWidgets.QProgressBar.setValue(self, value)

            # upload is complete, set the style
            if QtWidgets.QProgressBar.value(self) == 100:
                self.setStyleSheet(self.COMPLETED_STYLE)


class UploadButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super().__init__()
        QtWidgets.QPushButton.__init__(self, parent)
        self.set_ready()

    """
    Set various text and styles for the different states the upload button can be in
    """
    def set_ready(self):
        """
        Set the button to be blue out and ready to upload
        if there is no connection to IRIDA, show connection error instead and block
        :return:
        """
        self.setEnabled(True)
        self.setText("Start Upload")
        self.setStyleSheet("background-color: {}; color: black".format(colours.BLUE_LIGHT))

    def set_block(self):
        """
        Set the button to be greyed out and blocked
        if there is no connection to IRIDA, show connection error instead
        :return:
        """
        self.setEnabled(False)
        self.setText("Start Upload")
        self.setStyleSheet("background-color: grey; color: white")

    def set_uploading(self):
        self.setEnabled(False)
        self.setText("Uploading... See log for details.")
        self.setStyleSheet("background-color: {}; color: black".format(colours.YELLOW_LIGHT))

    def set_finished(self):
        self.setEnabled(False)
        self.setText("Upload Complete")
        self.setStyleSheet("background-color: {}; color: black".format(colours.GREEN_LIGHT))


class SampleTable(QtWidgets.QTableWidget):
    """
    This table extends the basic QTableWidget and manages the creation of Progress bars and other widgets in the table
    The widget is also responsible to handle the message passing of progress data to the Progress bar handler
    """
    # X index for the table
    TABLE_SAMPLE_NAME = 0
    TABLE_FILE_1 = 1
    TABLE_FILE_2 = 2
    TABLE_PROJECT = 3
    TABLE_PROGRESS = 4

    def __init__(self, parent=None):
        super().__init__()
        QtWidgets.QTableWidget.__init__(self, parent)
        self.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Sample Name", "File 1", "File 2", "Project", "Progress"])
        self.setColumnWidth(self.TABLE_SAMPLE_NAME, 170)
        self.setColumnWidth(self.TABLE_FILE_1, 200)
        self.setColumnWidth(self.TABLE_FILE_2, 200)
        self.setColumnWidth(self.TABLE_PROJECT, 70)
        self.setColumnWidth(self.TABLE_PROGRESS, 135)
        header = self.horizontalHeader()
        header.setSectionResizeMode(self.TABLE_PROGRESS, QtWidgets.QHeaderView.Stretch)
        # set up progress bar handler
        self._progress_bars = ProgressBarHandler(self)
        # subscribe the progress updates signal
        progress.signal_worker.progress_signal.connect(self._update_progress)

    def fill_table(self, sequencing_run, partial):
        """
        Given a SequencingRun, fill the table with data
        includes sample name, file names, project, and progress widget
        :param sequencing_run: SequencingRun object
        :param partial: Indicate already uploaded files in table
        :return:
        """
        # total number of samples
        sample_count = 0

        project_list = sequencing_run.project_list
        for project in project_list:
            sample_list = project.sample_list
            sample_count = sample_count + len(sample_list)

        # Set the row count to the number of samples in this run
        self.setRowCount(sample_count)
        # clear all the progress bars we may have created
        self._progress_bars.clear()

        y_index = 0
        for project in project_list:
            sample_list = project.sample_list
            for sample in sample_list:
                files = sample.sequence_file.file_list
                self.setItem(y_index, self.TABLE_SAMPLE_NAME,
                             QtWidgets.QTableWidgetItem(sample.sample_name))
                self.setItem(y_index, self.TABLE_FILE_1,
                             QtWidgets.QTableWidgetItem(os.path.basename(files[0])))
                if len(files) == 2:
                    self.setItem(y_index, self.TABLE_FILE_2,
                                 QtWidgets.QTableWidgetItem(os.path.basename(files[1])))
                self.setItem(y_index, self.TABLE_PROJECT, QtWidgets.QTableWidgetItem(project.id))

                new_progress_bar = self._progress_bars.add_bar(sample=sample.sample_name,
                                                               project=str(project.id))
                self.setCellWidget(y_index, self.TABLE_PROGRESS, new_progress_bar)
                print(sample.get_dict())
                if sample.skip and partial:
                    self._progress_bars.set_value(sample=sample.sample_name,
                                                  project=project.id,
                                                  value=100)

                y_index = y_index + 1

    def clear_table(self):
        """
        Wipes out tables contents and sets the row count back to 0
        :return:
        """
        self.clearContents()
        self.setRowCount(0)

    def _update_progress(self, data):
        """
        Updates the progress bars in the table
        receives the ProgressData object signal, and calls to the progress bar handler to update progres
        :param data: ProgressData
        :return:
        """
        self._progress_bars.set_value(sample=data.sample,
                                      project=data.project,
                                      value=data.progress)


class LogTextBox(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__()
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        # Set read only mode and hide
        self.setReadOnly(True)
        self.hide()

        # Setup logging handler
        handler = tools.QtHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S'))
        handler.setLevel(logging.INFO)
        # connect to the log/redraw function
        handler.message_writer.messageWritten.connect(self._write)
        # finally add it to the logging module
        logger.root_logger.addHandler(handler)

    def _write(self, text):
        """
        Adds the text given to the logger box, and repaints so it displays
        Used as a slot for emits
        :param text:
        :return:
        """
        self.appendPlainText(text)
        self.repaint()
