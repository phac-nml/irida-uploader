"""
This file has generic utility methods that can be used by all parsers

These methods can rely on the os module to function, and therefore not to be used with cloud environments.

They should be used as generic utilities for any new parser that is added to the project.
"""
import os
from csv import reader
import logging

from iridauploader.parsers import exceptions
from iridauploader import model


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

    if os.path.isfile(sample_sheet_file):
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


def find_directory_list(directory):
    """Find and return all directories in the specified directory.

    Arguments:
    directory -- the directory to find directories in

    Returns: a list of directories including current directory
    """

    # Checks if we can access to the given directory, return empty and log a warning if we cannot.
    if cannot_read_directory(directory):
        raise exceptions.DirectoryError("The directory is not readable, "
                                        "can not upload samples from this directory {}".format(directory),
                                        directory)

    dir_list = next(os.walk(directory))[1]  # Gets the list of directories in the directory
    full_dir_list = []
    for d in dir_list:
        full_dir_list.append(os.path.join(directory, d))
    return full_dir_list


def build_sequencing_run_from_samples(sample_list, metadata, sequence_run_type):
    """
    Create a SequencingRun object with full project/sample/sequence_file structure

    :param sample_list: List of Sample objects
    :param metadata: metadata dict to add to the run
    :param sequence_run_type: string identifier for sequencer type when generating api route
    :return: SequencingRun
    """

    logging.debug("Building SequencingRun from parsed data")

    # create list of projects and add samples to appropriate project
    project_list = []
    for sample in sample_list:
        project = None
        for p in project_list:
            if sample.get('sample_project') == p.id:
                project = p
        if project is None:
            project = model.Project(id=sample.get('sample_project'))
            project_list.append(project)

        project.add_sample(sample)

    sequence_run = model.SequencingRun(metadata=metadata,
                                       project_list=project_list,
                                       sequencing_run_type=sequence_run_type)
    logging.debug("SequencingRun built")
    return sequence_run


def get_file_list(directory):
    """
    Get the list of file names in the data directory

    :param directory: directory to search for files
    :return: list of file names in data directory
    """
    # verify that directory exists
    if not os.path.exists(directory):
        raise exceptions.DirectoryError("Could not list files, as directory does not exist.", directory)
    # Create a file list of the directory, only hit the os once
    file_list = next(os.walk(directory))[2]
    return file_list


def cannot_read_directory(directory):
    """
    Checks if a directory is missing the filesystem Readable flag,
    :param directory:
    :return: True if unreadable, False otherwise
    """
    return not os.access(directory, os.R_OK)
