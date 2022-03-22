import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets

from iridauploader.config import config
from iridauploader.parsers import supported_parsers

from iridauploader.gui import tools, colours


class ConfigDialog(QtWidgets.QDialog):
    """
    Configuration/Settings dialog window.

    This has multiple options that the user can change instead of using the config file.
    On opening the dialog the settings will be loaded from the config file.
    When the user accepts, or clicks "save and test", the settings will be written to the config file.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.debug("GUI: Setting up ConfigDialog")

        # Set dialog title
        self.setWindowTitle("Configure Settings")

        # Widgets
        self._btn_import_settings = QtWidgets.QPushButton("Import Configuration From File")
        self._client_id_label = QtWidgets.QLabel("Client ID")
        self._client_id = QtWidgets.QLineEdit()
        self._client_secret_label = QtWidgets.QLabel("Client Secret")
        self._client_secret = QtWidgets.QLineEdit()
        self._username_label = QtWidgets.QLabel("Username")
        self._username = QtWidgets.QLineEdit()
        self._password_label = QtWidgets.QLabel("Password")
        self._password = QtWidgets.QLineEdit()
        self._password.setEchoMode(QtWidgets.QLineEdit.Password)
        self._base_url_label = QtWidgets.QLabel("Base URL")
        self._base_url = QtWidgets.QLineEdit()
        self._parser_label = QtWidgets.QLabel("Parser")
        self._parser = QtWidgets.QComboBox()
        self._parser.addItems(supported_parsers)
        self._read_only_mode = QtWidgets.QCheckBox()
        self._read_only_mode_label = QtWidgets.QLabel("Read Only Mode")
        self._timeout_label = QtWidgets.QLabel("(ADVANCED) Timeout Seconds Per MB")
        self._timeout = QtWidgets.QSpinBox()
        self._min_file_size_label = QtWidgets.QLabel("(ADVANCED) Minimum File Size per file (KB)")
        self._min_file_size = QtWidgets.QSpinBox()
        self._min_file_size.setRange(0, 2147483647)  # set max as max allowed by QSpinBox

        self._btn_check_settings = QtWidgets.QPushButton("Save and Test Settings")
        self._settings_status = QtWidgets.QLineEdit()
        self._settings_status.setReadOnly(True)
        self._settings_status.setEnabled(False)
        self._settings_status.setStyleSheet("color: black")
        self._btn_accept = QtWidgets.QPushButton("Accept")
        self._btn_cancel = QtWidgets.QPushButton("Cancel")

        # connections
        self._btn_import_settings.clicked.connect(self._import_config_from_file)
        self._btn_check_settings.clicked.connect(self._check_connection_to_irida)
        self._btn_accept.clicked.connect(self._accept_and_exit)
        self._btn_cancel.clicked.connect(self._cancel_and_exit)

        # Set Layout and Geometry
        self.setLayout(self._layout())
        self.setGeometry(0, 0, 600, 300)

        # Init settings
        self._get_settings_from_file()
        self._contact_irida()

        # Error message popup
        self._error_message_box = QtWidgets.QMessageBox(parent=self)
        self._error_message_box.setText(
            'Config file was invalid. Please check your file and try again.<br>'
            '<a href="https://irida-uploader.readthedocs.io/en/stable/configuration.html">'
            'Click here for details on config files</a>'
        )
        self._error_message_box.setIcon(QtWidgets.QMessageBox.Critical)

    def _layout(self):
        """
        Layout widgets
        :return: QtWidgets.QVBoxLayout()
        """
        # base layout
        layout = QtWidgets.QVBoxLayout()
        # Load from file
        layout.addWidget(self._btn_import_settings)
        # Client ID
        client_id_layout = QtWidgets.QHBoxLayout()
        client_id_layout.addWidget(self._client_id_label)
        client_id_layout.addWidget(self._client_id)
        layout.addLayout(client_id_layout)
        # Client Secret
        client_secret_layout = QtWidgets.QHBoxLayout()
        client_secret_layout.addWidget(self._client_secret_label)
        client_secret_layout.addWidget(self._client_secret)
        layout.addLayout(client_secret_layout)
        # Username
        username_layout = QtWidgets.QHBoxLayout()
        username_layout.addWidget(self._username_label)
        username_layout.addWidget(self._username)
        layout.addLayout(username_layout)
        # Password
        password_layout = QtWidgets.QHBoxLayout()
        password_layout.addWidget(self._password_label)
        password_layout.addWidget(self._password)
        layout.addLayout(password_layout)
        # Base URL
        base_url_layout = QtWidgets.QHBoxLayout()
        base_url_layout.addWidget(self._base_url_label)
        base_url_layout.addWidget(self._base_url)
        layout.addLayout(base_url_layout)
        # Parser
        parser_layout = QtWidgets.QHBoxLayout()
        parser_layout.addWidget(self._parser_label)
        parser_layout.addWidget(self._parser)
        layout.addLayout(parser_layout)
        # Read Only
        read_only_layout = QtWidgets.QHBoxLayout()
        read_only_layout.addWidget(self._read_only_mode_label)
        read_only_layout.addWidget(self._read_only_mode)
        layout.addLayout(read_only_layout)
        # Timeout
        timeout_layout = QtWidgets.QHBoxLayout()
        timeout_layout.addWidget(self._timeout_label)
        timeout_layout.addWidget(self._timeout)
        layout.addLayout(timeout_layout)
        # Min file size
        min_file_size_layout = QtWidgets.QHBoxLayout()
        min_file_size_layout.addWidget(self._min_file_size_label)
        min_file_size_layout.addWidget(self._min_file_size)
        layout.addLayout(min_file_size_layout)
        # Buttons
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.addWidget(self._btn_check_settings)
        status_layout.addWidget(self._settings_status)
        layout.addLayout(status_layout)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self._btn_accept)
        button_layout.addWidget(self._btn_cancel)
        layout.addLayout(button_layout)

        return layout

    def _accept_and_exit(self):
        """
        Writes the settings to file and then closes
        :return:
        """
        self._write_settings_to_file()
        self._contact_irida()
        self.close()

    def _cancel_and_exit(self):
        """
        closes this widget
        :return:
        """
        self.close()

    def _get_settings_from_file(self):
        """
        Loads the config settings from file and fills the widgets
        :return:
        """
        config.setup()
        self._client_id.setText(config.read_config_option('client_id'))
        self._client_secret.setText(config.read_config_option('client_secret'))
        self._username.setText(config.read_config_option('username'))
        self._password.setText(config.read_config_option('password'))
        self._base_url.setText(config.read_config_option('base_url'))
        index = self._parser.findText(config.read_config_option('parser'))
        self._parser.setCurrentIndex(index)
        read_only_bool = config.read_config_option("readonly", bool, False)
        read_only_state = QtCore.Qt.Checked if read_only_bool else QtCore.Qt.Unchecked
        self._read_only_mode.setCheckState(read_only_state)
        timeout_int = config.read_config_option("timeout", int, 10)
        self._timeout.setValue(timeout_int)
        min_file_size_int = config.read_config_option("minimum_file_size", int, 0)
        self._min_file_size.setValue(min_file_size_int)

    def _write_settings_to_file(self):
        """
        Writes the settings in the config boxes to file
        :return:
        """
        config.set_config_options(client_id=self._client_id.text(),
                                  client_secret=self._client_secret.text(),
                                  username=self._username.text(),
                                  password=self._password.text(),
                                  base_url=self._base_url.text(),
                                  parser=self._parser.currentText(),
                                  readonly=self._read_only_mode.isChecked(),
                                  timeout=self._timeout.value(),
                                  minimum_file_size=self._min_file_size.value())
        config.write_config_options_to_file()

    def _contact_irida(self):
        """
        Attempts to connect to IRIDA
        Sets the style and text of the status widget to green/red to indicate connected/error
        :return:
        """
        if tools.is_connected_to_irida():
            self._settings_status.setText("Connection OK")
            self._settings_status.setStyleSheet("background-color: {}; color: black;".format(colours.GREEN_LIGHT))
            logging.info("Successfully connected to IRIDA")
        else:
            self._settings_status.setText("ERROR!")
            self._settings_status.setStyleSheet("background-color: {}; color: black;".format(colours.RED_LIGHT))
            logging.info("Error occurred while trying to connect to IRIDA")

    def _check_connection_to_irida(self):
        """
        Writes the settings in the boxes to the config file, and then tries to connect to IRIDA
        :return:
        """
        self._write_settings_to_file()
        self._contact_irida()

    def center_window(self):
        """
        sets the dialog position to the center of the parent
        :return:
        """
        qt_rectangle = self.frameGeometry()
        parent_geo = self.parent().frameGeometry().center()
        qt_rectangle.moveCenter(parent_geo)
        self.move(qt_rectangle.topLeft())

    def _import_config_from_file(self):
        """
        Opens dialog to choose file, exits early if no file is chosen or file is invalid
        Then, the files parameters are loaded and written to the default config file
        :return:
        """
        logging.debug("GUI CONFIG: _import_config_from_file clicked")
        # Open a file open dialog and get returned string
        config_file_path = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                 caption="Select Uploader Config File",
                                                                 filter="*.conf")[0]
        logging.debug("GUI CONFIG: result: " + config_file_path)
        # If user exits window without selecting a file, return early
        if config_file_path == "":
            logging.debug("GUI CONFIG: user canceled opening file")
            return

        # Do a first pass on the loaded file to see if it is valid.
        # If there is no exception, the file can be loaded normally.
        try:
            config.read_config_file_into_parser(config_file_path)
        except Exception:
            self._error_message_box.exec()
            return

        # set the config file to be the file the user selected
        config.set_config_file(config_file_path)
        # Load the properties into the window
        self._get_settings_from_file()
        # Reset the config file back to use default
        config.set_config_file(None)
        config.setup()
        # Write the settings from the user selected file to the default file
        self._write_settings_to_file()
        # Check connection with IRIDA
        self._contact_irida()
