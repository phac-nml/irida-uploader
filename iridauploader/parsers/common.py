import os
from csv import reader

from iridauploader.parsers import exceptions


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
        if not os.access(directory, os.W_OK):
            raise exceptions.DirectoryError("The directory is not writeable, "
                                            "can not upload samples from this directory {}".format(directory),
                                            directory)

        dir_list = next(os.walk(directory))[1]  # Gets the list of directories in the directory
        full_dir_list = []
        for d in dir_list:
            full_dir_list.append(os.path.join(directory, d))
        return full_dir_list
