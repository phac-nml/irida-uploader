import re
from os import path
from collections import OrderedDict
from copy import deepcopy
import logging

import iridauploader.model as model
from iridauploader.parsers import exceptions
from iridauploader.parsers import common


def parse_metadata(sample_sheet_file):

    """
    Parse all lines under [Header], [Reads] and [BCLConvert_Settings] in .csv file
    Lines under [Reads] are stored in a list with key name "readLengths"
    All other key names are translated according to the
        metadata_key_translation_dict

    arguments:
            sample_sheet_file -- path to UploadList.csv

    returns a dictionary containing the parsed key:pair values from .csv file
    """

    metadata_dict = {"readLengths": [], "indexCycles": []}

    csv_reader = common.get_csv_reader(sample_sheet_file)

    section = None

    for line in csv_reader:
        if "[Header]" in line or "[BCLConvert_Settings]" in line:
            section = "header"
            continue
        elif "[Reads]" in line:
            section = "reads"
            continue
        elif "[BCLConvert_Data]" in line:
            break
        elif line and line[0].startswith("["):
            section = "unknown"
            continue

        if not line or not line[0]:
            continue

        if not section:
            logging.debug("Sample sheet is missing important sections: no sections were found")
            raise exceptions.SampleSheetError("Sample sheet is missing important sections: no sections were found.",
                                              sample_sheet_file)
        elif section == "reads":
            if line[0] == "Read1Cycles" or line[0] == "Read2Cycles":
                metadata_dict["readLengths"].append(line[1])
            elif line[0] == "Index1Cycles" or line[0] == "Index2Cycles":
                metadata_dict["indexCycles"].append(line[1])

    # currently sends just the larger readLengths
    if len(metadata_dict["readLengths"]) == 2:
        metadata_dict["layoutType"] = "PAIRED_END"
    elif len(metadata_dict["readLengths"]) == 1:
        metadata_dict["layoutType"] = "SINGLE_END"
    else:
        logging.debug("The sample sheet has invalid [Reads] sections: [Reads] section should have 2 or 4 entries.")
        raise exceptions.SampleSheetError("The sample sheet has invalid [Reads] sections: "
                                          "[Reads] section should have 2 or 4 entries.",
                                          sample_sheet_file)
    metadata_dict["readLengths"] = max(metadata_dict["readLengths"])
    metadata_dict["indexCycles"] = max(metadata_dict["indexCycles"])

    return metadata_dict


def parse_sample_list(sample_sheet_file, run_data_directory, run_data_directory_file_list):
    """
    Creates a list of Sample Objects

    :param sample_sheet_file: Sample Sheet file
    :param run_data_directory: Data directory including run directory (e.g. my_run/Data/Intensities/BaseCalls)
    :param run_data_directory_file_list: The list of all files in the data directory
    :return: list of Sample objects
    """
    sample_list = _parse_samples(sample_sheet_file)

    for sample in sample_list:
        properties_dict = _parse_out_sequence_file(sample)
        # this is the Illumina-defined pattern for naming fastq files, from:
        # http://blog.basespace.illumina.com/2014/08/18/fastq-upload-in-now-available-in-basespace/
        file_pattern = "{sample_name}_S{sample_number}_L\\d{{3}}_R(\\d+)_\\S+\\.fastq.*$".format(
            sample_name=re.escape(sample.sample_name), sample_number=sample.sample_number)
        logging.info("Looking for files with pattern {}".format(file_pattern))
        regex = re.compile(file_pattern)
        pf_list = list(filter(regex.search, run_data_directory_file_list))
        if not pf_list:
            # OK. So we didn't find any files using the **correct** file name
            # definition according to Illumina. Let's try again with our deprecated
            # behaviour, where we didn't actually care about the sample number:
            file_pattern = "{sample_name}_S\\d+_L\\d{{3}}_R(\\d+)_\\S+\\.fastq.*$".format(
                sample_name=re.escape(sample.sample_name))
            logging.info("Looking for files with pattern {}".format(file_pattern))

            regex = re.compile(file_pattern)
            pf_list = list(filter(regex.search, run_data_directory_file_list))

            if not pf_list:
                # we **still** didn't find anything. It's pretty likely, then that
                # there aren't any fastq files in the directory that match what
                # the sample sheet says...
                raise exceptions.SequenceFileError(
                    ("The uploader was unable to find an files with a file name that ends with "
                     ".fastq.gz for the sample in your sample sheet with name {} in the directory {}. "
                     "This usually happens when the Illumina MiSeq Reporter tool "
                     "does not generate any FastQ data.").format(
                        sample.sample_name, run_data_directory))

        # List of files may be invalid if directory searching in has been modified by user
        if not _validate_pf_list(pf_list):
            raise exceptions.SequenceFileError(
                ("The following file list {} found in the directory {} is invalid. "
                 "Please verify the folder containing the sequence files matches the SampleSheet file").format(
                    pf_list, run_data_directory))

        # Add the dir to each file to create the full path
        for i in range(len(pf_list)):
            pf_list[i] = path.join(run_data_directory, pf_list[i])

        sq = model.SequenceFile(file_list=pf_list, properties_dict=properties_dict)
        sample.sequence_file = deepcopy(sq)

    return sample_list


def _validate_pf_list(file_list):
    """
    Checks if list of files is valid:

    arguments:
            file_list -- list of file names that are grouped together

    returns:
            True: 1 file in list
            True: 2 files in list, where one contains `R1` in the correct position and the other contains `R2`
            False: Number of files <1 or >2, or 2 files do not contain `R1`/`R2` correctly
    """
    if len(file_list) < 1:  # Invalid
        return False
    if len(file_list) > 2:  # We should never expect more than 2 files, a forward & backwards read
        return False
    elif len(file_list) == 1:  # single read, valid
        return True
    else:
        try:
            # check if one file is R1 and other is R2
            regex_filter = ".*_S\\d+_L\\d{3}_R(\\d+)_\\S+\\.fastq.*$"
            n1 = int(re.search(regex_filter, file_list[0]).group(1))
            n2 = int(re.search(regex_filter, file_list[1]).group(1))
            return (n1 != n2) and (n1 == 1 or n1 == 2) and (n2 == 1 or n2 == 2)
        except AttributeError:  # Attribute error means the file had invalid text in it
            return False


def _parse_samples(sample_sheet_file):

    """
    Parse all the lines under "[Data]" in .csv file
    Keys in sample_key_translation_dict have their values changed for
        uploading to REST API
    All other keys keep the same name that they have in .csv file

    arguments:
            sample_sheet_file -- path to UploadList.csv

    returns	a list containing Sample objects that have been created by a
        dictionary from the parsed out key:pair values from .csv file
    """

    logging.info("Reading data from sample sheet {}".format(sample_sheet_file))

    csv_reader = common.get_csv_reader(sample_sheet_file)
    # start with an ordered dictionary so that keys are ordered in the same
    # way that they are inserted.
    sample_dict = OrderedDict()
    sample_list = []

    sample_key_translation_dict = {
        'Sample_ID': 'sampleName',
        'Sample_Project': 'sample_project'
    }

    _parse_samples.sample_key_translation_dict = sample_key_translation_dict

    # initialize dictionary keys from first line (data headers/attributes)
    set_attributes = False
    for line in csv_reader:

        if set_attributes:
            for item in line:

                if item in sample_key_translation_dict:
                    key_name = sample_key_translation_dict[item]
                else:
                    key_name = item

                sample_dict[key_name] = ""

            break

        if "[BCLConvert_Data]" in line:
            set_attributes = True

    # fill in values for keys. line is currently below the [Data] headers
    for sample_number, line in enumerate(csv_reader):

        if len(sample_dict.keys()) != len(line):
            """
            if there is one more Data header compared to the length of
            data values then add an empty string to the end of data values
            i.e the Description will be empty string
            assumes the last Data header is going to be the Description
            this handles the case where the last trailing comma is trimmed

            Shaun said this issue may come up when a user edits the
            SampleSheet from within the MiSeq software
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
            sample_dict[key] = line[index].strip()  # assumes values are never empty

        new_sample_dict = deepcopy(sample_dict)
        new_sample_name = new_sample_dict['sampleName']
        del new_sample_dict['sampleName']

        sample = model.Sample(
            sample_name=new_sample_name,
            description="",
            sample_number=sample_number + 1,
            samp_dict=new_sample_dict)
        sample_list.append(sample)

    return sample_list


def _parse_out_sequence_file(sample):

    """
    Removes keys in argument sample that are not in sample_keys and
        stores them in sequence_file_dict

    arguments:
            sample -- Sample object
            the dictionary inside the Sample object is changed

    returns a dictionary containing keys not in sample_keys to be used to
        create a SequenceFile object
    """

    sample_keys = ["sampleName", "sample_project"]
    sequence_file_dict = {}
    sample_dict = sample.get_uploadable_dict()
    for key in list(sample_dict.keys()):
        if key not in sample_keys:
            sequence_file_dict[key] = sample_dict[key]

    return sequence_file_dict
