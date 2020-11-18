from os import path
from collections import OrderedDict
from copy import deepcopy
import logging

import iridauploader.model as model
from iridauploader.parsers import exceptions
from iridauploader.parsers import common


def parse_metadata(sample_list):
    """
    Determine if samples are paired or single end, and return metadata to match

    :param sample_list: List of Sample objects
    :return: metadata dictionary
    """
    # add the layout type to the sequencing run so we know if it is paired or single end
    if sample_list[0].sequence_file.is_paired_end():
        metadata = {'layoutType': 'PAIRED_END'}
    else:
        metadata = {'layoutType': 'SINGLE_END'}

    return metadata


def verify_sample_sheet_file_names_in_file_list(sample_sheet_file, run_data_directory_file_list):
    """
    Given a sample sheet, and a list of files in a directory,
    verify that all the files on the sheet exist in the file list

    If a file is missing, a SampleSheetError is raised

    :param sample_sheet_file:
    :param run_data_directory_file_list:
    :return:
    """
    sample_list = _parse_samples(sample_sheet_file)

    for sample in sample_list:
        sample_dict = sample.get_uploadable_dict()
        paired_end_read = len(sample_dict['File_Reverse']) > 0

        # Check if file names are in the files we found in the directory file list
        if sample_dict['File_Forward'] not in run_data_directory_file_list:
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file list in sample sheet file"
                 "".format(sample_dict['File_Forward'])),
                sample_sheet_file
            )
        if paired_end_read and sample_dict['File_Reverse'] not in run_data_directory_file_list:
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file list in sample sheet file"
                 "".format(sample_dict['File_Reverse'])),
                sample_sheet_file
            )


def build_sample_list_from_sample_sheet_with_abs_path(sample_sheet_file):
    """
    Create a list of Sample objects, where each SequenceFile object has an absolute file path

    :param sample_sheet_file:
    :return:
    """
    sample_list = _parse_samples(sample_sheet_file)
    # Data directory is used if file names on sample sheet are not absolute paths (in directory files)
    data_dir = path.dirname(sample_sheet_file)
    sample_sheet_dir_file_list = common.get_file_list(data_dir)

    for sample in sample_list:
        sample_dict = sample.get_uploadable_dict()
        paired_end_read = len(sample_dict['File_Reverse']) > 0

        # create file list of full paths
        file_list = []
        # If file is not an abspath already, make it an abspath from filename + data dir
        if path.isabs(sample_dict['File_Forward']):
            file_list.append(sample_dict['File_Forward'])
        elif sample_dict['File_Forward'] in sample_sheet_dir_file_list:
            sample_dict['File_Forward'] = path.join(path.abspath(data_dir), sample_dict['File_Forward'])

            file_list.append(sample_dict['File_Forward'])
        else:
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file in the directory {}"
                 "".format(sample_dict['File_Forward'], data_dir)),
                sample_sheet_file)

        # reverse file is same as for forward file
        if paired_end_read:
            if path.isabs(sample_dict['File_Reverse']):
                file_list.append(sample_dict['File_Reverse'])
            elif sample_dict['File_Reverse'] in sample_sheet_dir_file_list:
                sample_dict['File_Reverse'] = path.join(path.abspath(data_dir), sample_dict['File_Reverse'])
                file_list.append(sample_dict['File_Reverse'])
            else:
                raise exceptions.SampleSheetError(
                    ("Your sample sheet is malformed. {} Does not match any file in the directory {}"
                     "".format(sample_dict['File_Reverse'], data_dir)),
                    sample_sheet_file)

        # Create sequence file object and attach to sample
        sq = model.SequenceFile(file_list=file_list)
        sample.sequence_file = deepcopy(sq)

    return sample_list


def build_sample_list_from_sample_sheet_no_verify(sample_sheet_file):
    """
    Create a list of Sample objects, file existence is not verified before SequenceFile is created
    this is used when a pre-generated file list is used (e.g. cloud deployment)

    :param sample_sheet_file:
    :return:
    """
    sample_list = _parse_samples(sample_sheet_file)

    for sample in sample_list:

        sample_dict = sample.get_uploadable_dict()
        # create file list
        file_list = [sample_dict['File_Forward']]

        # if paired end add file to file list
        paired_end_read = len(sample_dict['File_Reverse']) > 0
        if paired_end_read:
            file_list.append(sample_dict['File_Reverse'])

        # Create sequence file object and attach to sample
        sq = model.SequenceFile(file_list=file_list)
        sample.sequence_file = deepcopy(sq)

    return sample_list


def only_single_or_paired_in_sample_list(sample_list):
    """
    Given a list of Sample objects, verifies there are only one type (single end or paired end)

    :param sample_list:
    :return: Boolean
    """
    has_single = False
    has_paired = False

    for sample in sample_list:
        if sample.sequence_file.is_paired_end():
            has_paired = True
        else:
            has_single = True

    return not (has_single and has_paired)


def _parse_samples(sample_sheet_file):

    """
    Parse all the lines under "[Data]" in .csv file

    arguments:
            sample_sheet_file -- path to SampleSheet.csv

    returns	a list containing Sample objects that have been created by a
        dictionary from the parsed out key:pair values from .csv file
    """

    logging.info("Reading data from sample sheet {}".format(sample_sheet_file))

    csv_reader = common.get_csv_reader(sample_sheet_file)
    # start with an ordered dictionary so that keys are ordered in the same
    # way that they are inserted.
    sample_dict = OrderedDict()
    sample_list = []

    sample_key_list = ['Sample_Name', 'Project_ID', 'File_Forward', 'File_Reverse']

    # initialize dictionary keys from first line (data headers/attributes)
    set_attributes = False
    for line in csv_reader:

        if set_attributes:
            for item in line:

                if item in sample_key_list:
                    key_name = item
                    sample_dict[key_name] = ""

            break

        if "[Data]" in line:
            set_attributes = True

    # fill in values for keys. line is currently below the [Data] headers
    for sample_number, line in enumerate(csv_reader):
        # if the line is empty (like a blank line at the end of the file) continue
        if not line:
            continue

        if len(sample_dict.keys()) != len(line):
            """
            if there is one more Data header compared to the length of
            data values then add an empty string to the end of data values
            i.e the File_Reverse will be empty string
            assumes the last Data header is going to be the File_Reverse
            this handles the case where the last trailing comma is trimmed when
            doing a single end run
            """
            if len(sample_dict.keys()) - len(line) == 1:
                line.append("")
            else:
                raise exceptions.SampleSheetError(
                    ("Your sample sheet is malformed. Expected to find {} "
                     "columns in the [Data] section, but only found {} columns "
                     "for line {}.".format(len(sample_dict.keys()), len(line), line)),
                    sample_sheet_file
                )

        for index, key in enumerate(sample_dict.keys()):
            value = line[index].strip()

            # Keys other than 'File_Reverse' cannot be empty
            if len(value) == 0:  # no value
                if key != 'File_Reverse':
                    raise exceptions.SampleSheetError(
                        ("Your sample sheet is malformed. {} in the [Data] section cannot be empty."
                         "".format(key)),
                        sample_sheet_file
                    )

            sample_dict[key] = value

        new_sample_dict = deepcopy(sample_dict)
        new_sample_name = new_sample_dict['Sample_Name']
        new_sample_project = new_sample_dict['Project_ID']
        new_sample_dict['sample_project'] = new_sample_project
        del new_sample_dict['Sample_Name']
        del new_sample_dict['Project_ID']

        sample = model.Sample(
            sample_name=new_sample_name,
            description="",
            sample_number=sample_number + 1,
            samp_dict=new_sample_dict)

        sample_list.append(sample)

    return sample_list
