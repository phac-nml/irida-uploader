from os import path, walk
from collections import OrderedDict
from copy import deepcopy
import logging

import iridauploader.model as model
from iridauploader.parsers import exceptions
from iridauploader.parsers import common


def build_sequencing_run_from_samples(sample_sheet_file):
    """
    Create a SequencingRun object with full project/sample/sequence_file structure

    :param sample_sheet_file:
    :return: SequencingRun
    """
    sample_list = _parse_sample_list(sample_sheet_file)

    logging.debug("Building SequencingRun from parsed data")

    # create list of projects and add samples to appropriate project
    project_list = []
    for sample_number, sample in enumerate(sample_list):
        # get data from data dict
        sample_name = sample['Sample_Name']
        project_id = sample['Project_ID']
        file_f = sample['File_Forward']
        file_r = sample['File_Reverse']

        project = None
        # see if project exists
        for p in project_list:
            if project_id == p.id:
                project = p
        # create project if it doesn't exitt yet
        if project is None:
            project = model.Project(id=project_id)
            project_list.append(project)

        # create sequence file
        if len(file_r) > 0:
            # paired end read
            sq = model.SequenceFile(properties_dict=None, file_list=[file_f, file_r])
        else:
            # single end read
            sq = model.SequenceFile(properties_dict=None, file_list=[file_f])

        # create sample
        sample_obj = model.Sample(sample_name=sample_name, sample_number=sample_number + 1)

        # add sequence file to sample
        sample_obj.sequence_file = deepcopy(sq)

        # add sample to project
        project.add_sample(sample_obj)

    # add the layout type to the sequencing run so we know if it is paired or single end
    if project_list[0].sample_list[0].sequence_file.is_paired_end():
        metadata = {'layoutType': 'PAIRED_END'}
    else:
        metadata = {'layoutType': 'SINGLE_END'}

    sequence_run = model.SequencingRun(metadata=metadata, project_list=project_list)
    logging.debug("SequencingRun built")
    return sequence_run


def _parse_sample_list(sample_sheet_file):
    """
    Creates a list of all sample data in the sample_sheet_file
    Verifies data is valid for uploading

    :param sample_sheet_file:
    :return: list of sample data dicts
    """
    sample_dict_list = _parse_samples(sample_sheet_file)

    data_dir = path.dirname(sample_sheet_file)
    data_dir_file_list = next(walk(data_dir))[2]  # Create a file list of the data directory, only hit the os once

    data_dir_file_list_full_path = []
    for file_name in data_dir_file_list:
        data_dir_file_list_full_path.append(path.join(path.abspath(data_dir), file_name))
    has_paired_end_read = False
    has_single_end_read = False

    logging.info("Verifying data parsed from sample sheet {}".format(sample_sheet_file))

    for sample_dict in sample_dict_list:

        paired_end_read = len(sample_dict['File_Reverse']) > 0
        # keep track if we have both paired and single end reads
        if paired_end_read:
            has_paired_end_read = True
        else:
            has_single_end_read = True

        # Check if file names are in the files we found in the directory
        if ((sample_dict['File_Forward'] not in data_dir_file_list) and (
                sample_dict['File_Forward'] not in data_dir_file_list_full_path)):
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file in the directory {}"
                 "".format(sample_dict['File_Forward'], data_dir)),
                sample_sheet_file
            )
        if ((paired_end_read and sample_dict['File_Reverse'] not in data_dir_file_list) and (
                paired_end_read and sample_dict['File_Reverse'] not in data_dir_file_list_full_path)):
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file in the directory {}"
                 "".format(sample_dict['File_Reverse'], data_dir)),
                sample_sheet_file
            )

        # Add the dir to each file to create the full path
        if sample_dict['File_Forward'] not in data_dir_file_list_full_path:
            sample_dict['File_Forward'] = path.join(data_dir, sample_dict['File_Forward'])
        if paired_end_read and sample_dict['File_Reverse'] not in data_dir_file_list_full_path:
            sample_dict['File_Reverse'] = path.join(data_dir, sample_dict['File_Reverse'])

    # Verify we don't have both single end and paired end reads
    if has_single_end_read and has_paired_end_read:
        raise exceptions.SampleSheetError(
            ("Your sample sheet is malformed. "
             "SampleSheet cannot have both paired end and single end runs. "
             "Make sure all samples are either paired or single."),
            sample_sheet_file
        )

    return sample_dict_list


def _parse_samples(sample_sheet_file):

    """
    Parse all the lines under "[Data]" in .csv file

    arguments:
            sample_sheet_file -- path to SampleSheet.csv

    returns a list containing dictionaries with the properties from the csv file
    """

    logging.info("Reading data from sample sheet {}".format(sample_sheet_file))

    csv_reader = common.get_csv_reader(sample_sheet_file)
    # start with an ordered dictionary so that keys are ordered in the same
    # way that they are inserted.
    sample_dict = OrderedDict()
    sample_dict_list = []

    sample_key_list = ['Sample_Name', 'Project_ID', 'File_Forward', 'File_Reverse']

    # initilize dictionary keys from first line (data headers/attributes)
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

        sample_dict_list.append(deepcopy(sample_dict))

    return sample_dict_list
