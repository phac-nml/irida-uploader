import os.path

import iridauploader.model as model
import iridauploader.config as config
from iridauploader.parsers.exceptions.file_size_error import FileSizeError


def validate_file_size_minimum(sequencing_run):
    """
    Validate the files in a SequencingRun object have the minimum file size requirement from the config

    :param sequencing_run: SequencingRun object to validate
    :return: ValidationResult object with list of errors if any
    """

    minimum_file_size = config.read_config_option("minimum_file_size", int, 0)

    validation_result = model.ValidationResult()

    for p in sequencing_run.project_list:
        for s in p.sample_list:
            # do validation of file size
            if not _file_size_is_valid(s.sequence_file, minimum_file_size):
                error_msg = "File size for sample `{}`is smaller than configured minimum of `{} KB`. " \
                            "Please verify your data.".format(s.sample_name, minimum_file_size)
                validation_result.add_error(FileSizeError(error_msg, s.sequence_file))

    return validation_result


def _file_size_is_valid(sequence_file, minimum_file_size):
    """
    Performs a os.path.getsize operation on the sequence file(s) on the sequence_file object
    if any files are less than the file minimum, return false, else return true

    :param sequence_file: SequenceFile object
    :param minimum_file_size: integer representing filesize in KB
    :return: boolean
    """
    for file_name in sequence_file.file_list:
        file_size_kb = os.path.getsize(file_name) / 1024
        if file_size_kb <= minimum_file_size:
            return False

    return True
