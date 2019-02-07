import os
import logging

from configparser import RawConfigParser, NoOptionError
from appdirs import user_config_dir
from collections import namedtuple

import global_settings

conf_parser = None
user_config_file = None


def setup():
    """
    Initialize and setup components for the configuration file
    :return:
    """

    global conf_parser
    global user_config_file
    # If a config file was passed as a parameter, use it, else use the default config directory
    if global_settings.config_file:
        user_config_file = global_settings.config_file
        if not os.path.exists(user_config_file):
            logging.error("Could not find config file: {}".format(user_config_file))
            exit(1)
    else:
        user_config_file = os.path.join(user_config_dir("irida-uploader"), "config.conf")

    conf_parser = RawConfigParser()
    logging.debug("User config file: " + user_config_file)

    # Set defaults for settings if file does not already exist
    SettingsDefault = namedtuple('SettingsDefault', ['setting', 'default_value'])

    default_settings = [SettingsDefault._make(["client_id", ""]),
                        SettingsDefault._make(["client_secret", ""]),
                        SettingsDefault._make(["username", ""]),
                        SettingsDefault._make(["password", ""]),
                        SettingsDefault._make(["base_url", ""]),
                        SettingsDefault._make(["parser", "directory"])]

    load_from_file = os.path.exists(user_config_file)
    # Loading config from file
    if load_from_file:
        try:
            logging.debug("Loading configuration settings from {}".format(user_config_file))

            conf_parser.read(user_config_file)

            for config in default_settings:
                if not conf_parser.has_option("Settings", config.setting):
                    conf_parser.set("Settings", config.setting, config.default_value)
        except:
            logging.warning("Error occurred when trying to load config file")
            logging.error("Config file {} is not valid.".format(user_config_file))
            exit(1)

    # Create a new user config file and fill with defaults
    if not load_from_file:
        logging.info("Creating a new config file.")
        conf_parser.add_section("Settings")

        if not os.path.exists(os.path.dirname(user_config_file)):
            os.makedirs(os.path.dirname(user_config_file))

        for config in default_settings:
            conf_parser.set("Settings", config.setting, config.default_value)

        with open(user_config_file, 'w') as config_file:
            conf_parser.write(config_file)

        logging.info("Config File Created: " + str(user_config_file))
        logging.info("Please edit your config file to connect to IRIDA")


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

    global conf_parser
    try:
        if not expected_type:
            value = conf_parser.get("Settings", key)
            logging.debug("Got configuration for key {}: {}".format(key, value))
            return conf_parser.get("Settings", key)
        elif expected_type is bool:
            return conf_parser.getboolean("Settings", key)
    except (ValueError, NoOptionError) as e:
        if default_value:
            return default_value
        else:
            raise


def write_config_option(field_name, field_value):
    """
    Writes an option to the configuration file.

    :param field_name: Field to change the value of
    :param field_value: Value to write to file
    :return: None
    """
    global conf_parser
    global user_config_file
    conf_parser.set("Settings", field_name, field_value)

    with open(user_config_file, 'w') as c_file:
        conf_parser.write(c_file)
