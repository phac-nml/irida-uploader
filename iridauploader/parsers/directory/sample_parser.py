from os import path, walk
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


def parse_sample_list(sample_sheet_file, run_data_directory_file_list):
    """
    Creates a list of all sample data in the sample_sheet_file
    Verifies data is valid for uploading

    :param sample_sheet_file:
    :param run_data_directory_file_list: list of all files
    :return: list of Sample objects
    """
    sample_list = _parse_samples(sample_sheet_file)

    data_dir = path.dirname(sample_sheet_file)

    data_dir_file_list_full_path = []
    for file_name in run_data_directory_file_list:
        data_dir_file_list_full_path.append(path.join(path.abspath(data_dir), file_name))

    has_paired_end_read = False
    has_single_end_read = False

    logging.info("Verifying data parsed from sample sheet {}".format(sample_sheet_file))

    for sample in sample_list:

        sample_dict = sample.get_uploadable_dict()

        paired_end_read = len(sample_dict['File_Reverse']) > 0
        # keep track if we have both paired and single end reads
        if paired_end_read:
            has_paired_end_read = True
        else:
            has_single_end_read = True

        # Check if file names are in the files we found in the directory
        if ((sample_dict['File_Forward'] not in run_data_directory_file_list) and (
                sample_dict['File_Forward'] not in data_dir_file_list_full_path)):
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file in the directory {}"
                 "".format(sample_dict['File_Forward'], data_dir)),
                sample_sheet_file
            )
        if ((paired_end_read and sample_dict['File_Reverse'] not in run_data_directory_file_list) and (
                paired_end_read and sample_dict['File_Reverse'] not in data_dir_file_list_full_path)):
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file in the directory {}"
                 "".format(sample_dict['File_Reverse'], data_dir)),
                sample_sheet_file
            )

        # create file list of full paths
        file_list = []
        # Add the dir to each file to create the full path
        if sample_dict['File_Forward'] not in data_dir_file_list_full_path:
            sample_dict['File_Forward'] = path.join(data_dir, sample_dict['File_Forward'])
            file_list.append(sample_dict['File_Forward'])
        if paired_end_read and sample_dict['File_Reverse'] not in data_dir_file_list_full_path:
            sample_dict['File_Reverse'] = path.join(data_dir, sample_dict['File_Reverse'])
            file_list.append(sample_dict['File_Reverse'])

        # Create sequence file object and attach to sample
        sq = model.SequenceFile(file_list=file_list)
        sample.sequence_file = deepcopy(sq)

    # Verify we don't have both single end and paired end reads
    if has_single_end_read and has_paired_end_read:
        raise exceptions.SampleSheetError(
            ("Your sample sheet is malformed. "
             "SampleSheet cannot have both paired end and single end runs. "
             "Make sure all samples are either paired or single."),
            sample_sheet_file
        )

    return sample_list


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
            if len(value) is 0:  # no value
                if key != 'File_Reverse':
                    raise exceptions.SampleSheetError(
                        ("Your sample sheet is malformed. {} in the [Data] section cannot be empty."
                         "".format(key)),
                        sample_sheet_file
                    )

            sample_dict[key] = value

        sample_key_list = ['Sample_Name', 'Project_ID', 'File_Forward', 'File_Reverse']

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
