import iridauploader.model as model
from iridauploader.parsers.exceptions.sequence_file_error import SequenceFileError


def validate_uniform_file_count(sequencing_run):
    """
    Validate the files in a SequencingRun object are all either in pairs, or single files

    :param sequencing_run: SequencingRun object to validate
    :return: ValidationResult object with list of errors if any
    """
    paired = sequencing_run.is_paired_end()
    expected_file_count = 2 if paired else 1

    validation_result = model.ValidationResult()

    for p in sequencing_run.project_list:
        for s in p.sample_list:
            # do validation of files
            if not _matching_find_count(s, paired):
                error_msg = "File count for sample `{}` does not match the expected file count `{}`. " \
                            "Please verify your data.".format(s.sample_name, expected_file_count)
                validation_result.add_error(SequenceFileError(error_msg))

    return validation_result


def _matching_find_count(sample, paired):
    """
    checks paired end / single end file matching on sample

    :param sample: Sample object
    :param paired: boolean
    :return: boolean
    """
    return sample.sequence_file.is_paired_end() == paired
