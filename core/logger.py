from appdirs import user_log_dir
import os
import logging.handlers


log_directory_name = "irida_uploader"
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

logging.info("Logging to file in: " + user_log_dir(log_directory_name))
