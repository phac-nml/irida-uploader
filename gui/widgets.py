import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets

import os

from core import logger
import progress

from . import colours, tools


class ProgressBarHandler:
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

    def add_bar(self, sample, project, paired_end_run=False):
        """
        Create a new progress bar given a sample and project id
        :param sample: sample name
        :param project: project id
        :param paired_end_run: Boolean, if this sample uses paired end files
        :return: QUploadProgressBar
        """
        key = self._get_key(sample, project)
        bar = self.QUploadProgressBar(parent=self._q_parent, paired_end_run=paired_end_run)
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

        def __init__(self, parent=None, paired_end_run=False):
            super().__init__()
            QtWidgets.QProgressBar.__init__(self, parent)
            self.setStyleSheet(self.DEFAULT_STYLE)
            self._paired_end_run = paired_end_run

        def setValue(self, value):
            """
            Sets the value of of the progress bar
            If its a paired end read, it will progress to 50% for the first file, and the remaining 50% for the second
            :param value: int or float
            :return: None
            """
            if self._paired_end_run:  # 2 files being uploaded
                if self.value() < 50:  # First file uploading
                    QtWidgets.QProgressBar.setValue(self, int(0.5 * value))
                else:  # Second file uploading
                    QtWidgets.QProgressBar.setValue(self, int(50 + (0.5 * value)))
            else:  # 1 file being uploaded
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

    def fill_table(self, sequencing_run):
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
                                                               project=str(project.id),
                                                               paired_end_run=(len(files) == 2))
                self.setCellWidget(y_index, self.TABLE_PROGRESS, new_progress_bar)

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
