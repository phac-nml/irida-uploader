import json
import os

from model.directory_status import DirectoryStatus


def get_directory_status(directory, sample_sheet):
    """
    Gets the directory status based off using '.miseqUploaderInfo' files to track progress

    :param directory: the directory to search for a run
    :param sample_sheet: optional param: if a sample sheet is required for a run,
        the file name for the sample sheet can be added here to validate that it exists
    :return: directory and status dictionary
    """
    result = DirectoryStatus(directory)

    if not os.access(directory, os.W_OK):
        result.status = 'invalid'
        result.message = 'Directory cannot be accessed. Please check permissions'
        return result

    file_list = next(os.walk(directory))[2]  # Gets the list of files in the directory
    if sample_sheet not in file_list:
        result.status = 'invalid'
        result.message = 'Directory has no valid sample sheet file with the name {}'.format(sample_sheet)
        return result

    if '.miseqUploaderInfo' not in file_list:  # no .miseqUploaderInfo file yet, has not been uploaded
        result.status = 'new'
        return result

    # Must check status of upload to determine if upload is completed
    uploader_info_file = os.path.join(directory, '.miseqUploaderInfo')
    with open(uploader_info_file, "rb") as reader:
        data = reader.read().decode()
        # import pdb; pdb.set_trace()
        info_file = json.loads(data)
        complete = info_file["Upload Status"] == "Complete"  # if True, done uploading, if False, partially done
        if complete:
            result.status = 'complete'
        else:
            result.status = 'partial'
        return result
