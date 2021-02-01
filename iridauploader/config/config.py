import os
import logging

from configparser import RawConfigParser, NoOptionError
from appdirs import user_config_dir
from collections import namedtuple

_conf_parser = None
_user_config_file = None

_default_user_config_file_path = os.path.join(user_config_dir("irida-uploader"), "config.conf")

# set an override config file in the source code directory, if it exists it will be used instead of getting it from user
_override_config_file_path = os.path.realpath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), os.path.pardir, "config.conf"))


def set_config_file(config_file):
    """
    Public function to allow other modules to change the config file
    This does not load the settings into the config parser
    :param config_file:
    :return:
    """
    global _user_config_file
    _user_config_file = config_file


def _init_config_parser():
    """
    Creates the RawConfigParser object, adds the fields and fills with default/empty values
    :return:
    """
    global _conf_parser
    # Create a new config parser
    _conf_parser = RawConfigParser()
    # Put all options under a Settings Header
    _conf_parser.add_section("Settings")

    # Create defaults tuple
    SettingsDefault = namedtuple('SettingsDefault', ['setting', 'default_value'])
    default_settings = [SettingsDefault._make(["client_id", ""]),
                        SettingsDefault._make(["client_secret", ""]),
                        SettingsDefault._make(["username", ""]),
                        SettingsDefault._make(["password", ""]),
                        SettingsDefault._make(["base_url", ""]),
                        SettingsDefault._make(["parser", "directory"]),
                        SettingsDefault._make(["readonly", False]),
                        SettingsDefault._make(["delay", 0]),
                        SettingsDefault._make(["timeout", 10])]  # default timeout scale is 10 seconds per mb
    # add defaults to config parser
    for config in default_settings:
        _conf_parser.set("Settings", config.setting, config.default_value)


def _create_new_config_file():
    """
    Tries to create a new config file
    Exit's if the file already exists, or a user config file is already set
    This only gets used to create a fresh default configuration file
    Fills the new file with defaults
    :return:
    """
    global _user_config_file
    if _user_config_file is not None:
        logging.error("Trying to create new config file when config file as already been set. Exiting")
        return

    _user_config_file = _default_user_config_file_path

    # Create path to file if it doesn't exit yet
    if not os.path.exists(os.path.dirname(_user_config_file)):
        os.makedirs(os.path.dirname(_user_config_file))
    # return if the file already exists
    if os.path.exists(_user_config_file):
        logging.error("File already exits, cannot create a new file")
        return

    # init the config parser with default values
    global _conf_parser
    with open(_user_config_file, 'w') as config_file:
        _conf_parser.write(config_file)

    logging.info("Config File Created: " + str(_user_config_file))
    logging.info("Please edit your config file to connect to IRIDA")


def _load_config_from_file():
    """
    Verifies file exists, and loads data from file into the config parser
    :return:
    """
    global _user_config_file

    if not os.path.exists(_user_config_file):
        logging.error("Config File {} does not exist, exiting".format(_user_config_file))
        exit(1)

    try:
        _conf_parser.read(_user_config_file)
    except Exception:
        logging.warning("Error occurred when trying to load config file")
        logging.error("Config file {} is not valid.".format(_user_config_file))
        exit(1)

    logging.info("Config loaded from file {}".format(_user_config_file))


def set_config_options(client_id=None,
                       client_secret=None,
                       username=None,
                       password=None,
                       base_url=None,
                       parser=None,
                       readonly=None,
                       delay=None,
                       timeout=None):
    """
    Updates the config options for all not None parameters
    :param client_id:
    :param client_secret:
    :param username:
    :param password:
    :param base_url:
    :param parser:
    :param readonly:
    :param delay:
    :param timeout:
    :return:
    """
    global _conf_parser
    if _conf_parser is None:
        logging.error("Config Parser has not been init, exiting")
        exit(1)

    if client_id:
        logging.debug("Setting 'client_id' config to {}".format(client_id))
        _update_config_option("client_id", client_id)
    if client_secret:
        logging.debug("Setting 'client_secret' config to {}".format(client_secret))
        _update_config_option("client_secret", client_secret)
    if username:
        logging.debug("Setting 'username' config to {}".format(username))
        _update_config_option("username", username)
    if password:
        logging.debug("Setting 'password' config")
        _update_config_option("password", password)
    if base_url:
        logging.debug("Setting 'base_url' config to {}".format(base_url))
        _update_config_option("base_url", base_url)
    if parser:
        logging.debug("Setting 'parser' config to {}".format(parser))
        _update_config_option("parser", parser)
    # since readonly is a bool and not a string, we need to check that is is not None, not just not True
    if readonly is not None:
        logging.debug("Setting 'readonly' config to {}".format(readonly))
        _update_config_option("readonly", readonly)
    if delay is not None:
        # delay is always an int
        logging.debug("Setting 'delay' config to {}".format(delay))
        _update_config_option('delay', delay)
    if timeout is not None:
        # timeout is always an int
        logging.debug("Setting 'timeout' config to {}".format(timeout))
        _update_config_option('timeout', timeout)


def setup():
    """
    Initialize and setup components for the configuration file
    Creates a new conf parser, and loads from user_config_file or default config file
    If the default file is used but doesn't exist, it will be created and the program will exit
    :return:
    """
    global _conf_parser
    global _user_config_file
    global _default_user_config_file_path
    global _override_config_file_path

    _init_config_parser()
    # If a config file is set, inform user
    if _user_config_file:
        logging.info("Config file set to {}".format(_user_config_file))
    # if the override config file exists, use it over the default
    elif os.path.exists(_override_config_file_path):
        logging.info("Override config file found. Using file: {}".format(_override_config_file_path))
        _user_config_file = _override_config_file_path
    # If a config file was not set, create a new file
    elif not os.path.exists(_default_user_config_file_path):
        logging.info("No config file found, creating a new file {}".format(_default_user_config_file_path))
        _create_new_config_file()
    # Use the default file as the user config file
    else:
        logging.info("Using default config file {}".format(_default_user_config_file_path))
        _user_config_file = _default_user_config_file_path

    # Load from file
    _load_config_from_file()


def read_config_option(key, expected_type=None, default_value=None):
    """Read the specified value from the configuration file.

    Args:
        key: the name of the key to read from the config file.
        expected_type: read the config option as the specified type (if specified)
        default_value: if the key doesn't exist, just return the default value.
            If the default value is not specified, the function will throw whatever
            error was raised by the configuration parser
    """
    logging.debug("Reading config option {} with expected type {}".format(key, expected_type))

    global _conf_parser
    try:
        if not expected_type:
            value = _conf_parser.get("Settings", key)
            logging.debug("Got configuration for key {}: {}".format(key, value))
            return _conf_parser.get("Settings", key)
        elif expected_type is int:
            res = _conf_parser.get("Settings", key)
            logging.debug("Got configuration for key {}: {}".format(key, res))
            # Return int, or string evaluated to int, or NameError exception otherwise
            if type(res) is int:
                return res
            elif type(res) is str:
                try:
                    return int(res)
                except Exception:
                    raise NameError
        elif expected_type is bool:
            res = _conf_parser.get("Settings", key)
            logging.debug("Got configuration for key {}: {}".format(key, res))
            # Return bool, or string evaluated to bool, or NameError exception otherwise
            if type(res) is bool:
                return res
            elif type(res) is str:
                return eval(res)
            else:
                raise NameError
    except (ValueError, NameError, NoOptionError):
        if default_value:
            return default_value
        else:
            raise


def _update_config_option(field_name, field_value):
    """
    Sets an option in the config parser (Does not write to file)
    :param field_name: Field to change the value of
    :param field_value: Value to change to
    :return:
    """
    global _conf_parser
    logging.debug("Setting [" + field_name + "] to [" + str(field_value) + "]")
    _conf_parser.set("Settings", field_name, field_value)


def write_config_options_to_file():
    """
    Writes all options in the config parser to config file

    :return: None
    """
    global _conf_parser
    global _user_config_file
    with open(_user_config_file, 'w') as c_file:
        _conf_parser.write(c_file)
