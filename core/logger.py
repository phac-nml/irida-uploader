from appdirs import user_log_dir
import os
import logging.handlers

import global_settings


# Normal base logging directory name
log_directory_name = "irida_uploader"
# When running tests, the Makefile creates an environment variable IRIDA_UPLOADER_TEST to 'True'
# If it exists then we are running a test and should be logging to the test logs directory
if os.environ.get('IRIDA_UPLOADER_TEST'):
    log_directory_name = "irida_uploader_test"
# Use systems default logging path, and append our named directory
log_file_path = os.path.join(user_log_dir(log_directory_name), 'irida-uploader.log')

if not os.path.exists(user_log_dir(log_directory_name)):
    os.makedirs(user_log_dir(log_directory_name))

# Looks something like this:
# 2019-02-07 14:50:02 INFO     Log message goes here...
log_format = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# setup root logger
root_logger = logging.getLogger()
root_logger.handlers = []
logging.basicConfig(
    level=logging.NOTSET,  # Default to highest (NOTSET) level, so everything is possible to be logged by handlers
    handlers=[logging.NullHandler()]  # Default log to Null, so that we can handle it manually
)

# Log to file
rotating_file_handler = logging.handlers.RotatingFileHandler(
    filename=log_file_path,
    maxBytes=(1024 * 1024 * 1024 * 10),  # 10GB max file size
    backupCount=100,
)
rotating_file_handler.setLevel(logging.DEBUG)
rotating_file_handler.setFormatter(log_format)
root_logger.addHandler(rotating_file_handler)

# Log to the user
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(log_format)
root_logger.addHandler(console)

global_settings.log_file = user_log_dir(log_directory_name)


directory_logger = None


def add_log_to_directory(directory):
    logging.info("Adding log file to {}".format(directory))
    log_file = os.path.join(directory, 'irida-uploader.log')
    global directory_logger
    directory_logger = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=(1024 * 1024 * 1024 * 10),  # 10GB max file size
        backupCount=100,
    )
    directory_logger.setLevel(logging.INFO)
    directory_logger.setFormatter(log_format)
    root_logger.addHandler(directory_logger)


def remove_directory_logger():
    global directory_logger
    root_logger.removeHandler(directory_logger)
    logging.info("Stopped active logging to run directory")
