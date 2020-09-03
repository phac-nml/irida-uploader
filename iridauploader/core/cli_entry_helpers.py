import iridauploader.progress as progress


def set_and_write_directory_status(directory_status, status, message=None):
    """
    Given a DirectoryStatus object, sets the status and message, and then writes to the directory status directory

    :param directory_status: DirectoryStatus object
    :param status: a valid DirectoryStatus status
    :param message: string
    :return:
    """
    directory_status.status = status
    directory_status.message = message
    progress.write_directory_status(directory_status)
