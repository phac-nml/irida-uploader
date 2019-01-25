from os import path, walk
from csv import reader
from collections import OrderedDict
from copy import deepcopy
import logging

import model
from .. import exceptions


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
        sample_obj = model.Sample(sample_name=sample_name, sample_number=sample_number+1)

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
        if sample_dict['File_Forward'] not in data_dir_file_list:
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file in the directory {}"
                 "".format(sample_dict['File_Forward'], data_dir)),
                sample_sheet_file
            )
        if paired_end_read and sample_dict['File_Reverse'] not in data_dir_file_list:
            raise exceptions.SampleSheetError(
                ("Your sample sheet is malformed. {} Does not match any file in the directory {}"
                 "".format(sample_dict['File_Reverse'], data_dir)),
                sample_sheet_file
            )

        # Add the dir to each file to create the full path
        sample_dict['File_Forward'] = path.join(data_dir, sample_dict['File_Forward'])
        if paired_end_read:
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

    csv_reader = get_csv_reader(sample_sheet_file)
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
            if len(value) is 0: # no value
                if key != 'File_Reverse':
                    raise exceptions.SampleSheetError(
                        ("Your sample sheet is malformed. {} in the [Data] section cannot be empty."
                         "".format(key)),
                        sample_sheet_file
                    )

            sample_dict[key] = value

        sample_dict_list.append(deepcopy(sample_dict))

    return sample_dict_list


def get_csv_reader(sample_sheet_file):

    """
    tries to create a csv.reader object which will be used to
        parse through the lines in SampleSheet.csv
    raises an error if:
            sample_sheet_file is not an existing file
            sample_sheet_file contains null byte(s)

    arguments:
            data_dir -- the directory that has SampleSheet.csv in it

    returns a csv.reader object
    """

    if path.isfile(sample_sheet_file):
        csv_file = open(sample_sheet_file, "r")
        # strip any trailing newline characters from the end of the line
        # including Windows newline characters (\r\n)
        csv_lines = [x.rstrip('\n') for x in csv_file]
        csv_lines = [x.rstrip('\r') for x in csv_lines]

        # open and read file in binary then send it to be parsed by csv's reader
        csv_reader = reader(csv_lines)
    else:
        raise exceptions.SampleSheetError("Sample sheet cannot be parsed as a CSV file because it's not a regular file.",
                                          sample_sheet_file)

    return csv_reader
