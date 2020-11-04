from appdirs import user_log_dir
import os
import logging.handlers


# Normal base logging directory name
log_directory_name = "irida-uploader"
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

# manages the logging directory
# only one directory can have a logger at a time
directory_logger = None


def add_log_to_directory(directory):
    """
    Starts up a logging handler that creates a log file in the directory being uploaded

    :param directory: directory to create a logger in
    :return: None
    """
    global directory_logger

    # If there is already a directory logger in place, throw an exception
    if directory_logger:
        logging.error("A directory logger already exists!")
        raise Exception("ERROR:add_log_to_directory: A directory logger already exists!")

    logging.info("Adding log file to {}".format(directory))
    log_file = os.path.join(directory, 'irida-uploader.log')
    directory_logger = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=(1024 * 1024 * 1024 * 10),  # 10GB max file size
        backupCount=100,
    )
    directory_logger.setLevel(logging.INFO)
    directory_logger.setFormatter(log_format)
    root_logger.addHandler(directory_logger)


def remove_directory_logger():
    """
    Deletes the existing directory logger so logging stops

    :return: None
    """
    global directory_logger
    root_logger.removeHandler(directory_logger)
    directory_logger = None
    logging.info("Stopped active logging to run directory")


def get_user_log_dir():
    return user_log_dir(log_directory_name)
