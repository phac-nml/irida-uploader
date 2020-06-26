from iridauploader.parsers import exceptions
from iridauploader.parsers import common
import iridauploader.model as model


def validate_sample_sheet(sample_sheet_file):

    """
    Checks if the given sample_sheet_file can be parsed
    Requires [Header] because it contains Workflow
    Requires [Data] for creating Sample objects and requires
        Sample_ID, Sample_Name, Sample_Project and Description table headers

    arguments:
            sample_sheet_file -- path to SampleSheet.csv

    returns ValidationResult object - stores list of string error messages
    """

    csv_reader = common.get_csv_reader(sample_sheet_file)

    v_res = model.ValidationResult()

    all_data_headers_found = False
    data_sect_found = False
    header_sect_found = False
    reads_sect_found = False
    check_data_headers = False

    # status of required data headers
    found_data_headers = {
        "Sample_ID": False,
        "Sample_Name": False,
        "Sample_Project": False}

    for line in csv_reader:

        if "[Data]" in line:
            data_sect_found = True
            check_data_headers = True  # next line contains data headers

        elif "[Header]" in line:
            header_sect_found = True

        elif "[Reads]" in line:
            reads_sect_found = True

        elif check_data_headers:

            for data_header in found_data_headers.keys():
                if data_header in line:
                    found_data_headers[data_header] = True

            # if all required dataHeaders are found
            if all(found_data_headers.values()):
                all_data_headers_found = True

            check_data_headers = False

    if not all([header_sect_found, data_sect_found, all_data_headers_found, reads_sect_found]):

        if header_sect_found is False:
            v_res.add_error(exceptions.SampleSheetError("[Header] section not found in SampleSheet", sample_sheet_file))

        if data_sect_found is False:
            v_res.add_error(exceptions.SampleSheetError("[Data] section not found in SampleSheet", sample_sheet_file))

        if reads_sect_found is False:
            v_res.add_error(exceptions.SampleSheetError("[Reads] section not found in SampleSheet", sample_sheet_file))

        if all_data_headers_found is False:
            missing_str = ""
            for data_header in found_data_headers:
                if found_data_headers[data_header] is False:
                    missing_str = missing_str + data_header + ", "

            missing_str = missing_str[:-2]  # remove last ", "
            v_res.add_error(exceptions.SampleSheetError("Missing required data header(s): " + missing_str,
                                                        sample_sheet_file))

    return v_res
