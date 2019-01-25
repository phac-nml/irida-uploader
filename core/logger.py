from appdirs import user_log_dir
import os
import logging


log_directory_name = "irida_uploader"
log_file_name = 'irida-uploader.log'

if not os.path.exists(user_log_dir(log_directory_name)):
    os.makedirs(user_log_dir(log_directory_name))

log_format = '%(asctime)s %(levelname)-8s %(message)s'

root_logger = logging.getLogger()
root_logger.handlers = []
# Log to file
logging.basicConfig(
        format=log_format,
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=os.path.join(user_log_dir(log_directory_name), log_file_name),
        filemode='w')

# Log to the user
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(log_format))
root_logger.addHandler(console)
