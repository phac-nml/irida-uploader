#Common Errors

Here are some common error messages you might see when trying to upload.

##Parsing

No runs could be found in a directory: Double check that that is the directory with your sample sheet, and that you are using the right parser.

Alternatively, you may be using the wrong parser, check your configuration parser matches the type of run/directory you are trying to upload.

    ERROR    ERROR! An error occurred with directory 'tests/parsers/miseq/no_dirs/', with message: The directory tests/parsers/miseq/no_dirs/ has no sample sheet file in the MiSeq format with the name SampleSheet.csv
<br>
Invalid sample sheet. Problems were found when trying to parse your sample sheet.

Pay close attention to the error list

    ERROR    Errors occurred while getting sample sheet
    ERROR    ERROR! Errors occurred during validation with message: Errors occurred while getting sample sheet

    ERROR    Error list: [SampleSheetError('[Header] section not found in SampleSheet', 'tests/parsers/miseq/invalid_sample_sheet/SampleSheet.csv'),
        SampleSheetError('[Data] section not found in SampleSheet', 'tests/parsers/miseq/invalid_sample_sheet/SampleSheet.csv'),
        SampleSheetError('[Reads] section not found in SampleSheet', 'tests/parsers/miseq/invalid_sample_sheet/SampleSheet.csv'),
        SampleSheetError('Missing required data header(s): Sample_ID, Sample_Name, Sample_Project, Description', 'tests/parsers/miseq/invalid_sample_sheet/SampleSheet.csv')]
<br>
Files matching the sample name could not be found, check your sample sheet and file names

    ERROR    Errors occurred while building sequence run from sample sheet
    ERROR    ERROR! Errors occurred during validation with message: Errors occurred while building sequence run from sample sheet
    ERROR    Error list: [SequenceFileError('The uploader was unable to find an files with a file name that ends with .fastq.gz for the sample in your sample sheet with name 011111 in the directory tests/parsers/miseq/ngs_not_pf_list/Data/Intensities/BaseCalls. This usually happens when the Illumina MiSeq Reporter tool does not generate any FastQ data.',)]
<br>
To many, or not enough files found with names matching the sample name.

    ERROR    Errors occurred while building sequence run from sample sheet
    ERROR    ERROR! Errors occurred during validation with message: Errors occurred while building sequence run from sample sheet
    ERROR    Error list: [SequenceFileError("The following file list ['01-1111_S1_L001_R1_001.fastq.gz', '01-1111_S1_L001_R3_001.fastq.gz', '01-1111_S1_L001_R2_001.fastq.gz'] found in the directory tests/parsers/miseq/ngs_not_valid_pf_list/Data/Intensities/BaseCalls is invalid. Please verify the folder containing the sequence files matches the SampleSheet file",)]
<br>
Invalid haracter in sample name (such as a space). This is not allowed on IRIDA

    ERROR    Did not create sample on server. Response code is '400' and error message is '{"sampleName":["The name you have supplied contains a space character. Names must NOT include the space character and the following: ? ( ) [ ] /  = + < > : ; \" ' , * ^ | & ."]}'

##Uploading
<br>
Invalid credentials in configuration file, double check that your configuration file is correct

    ERROR    Can not get access token from IRIDA
    ERROR    ERROR! Could not initialize irida api.
    ERROR    Errors: ('Could not get access token from IRIDA. Credentials may be incorrect. IRIDA '
    "returned with error message: ('Decoder failed to handle access_token with "
    'data as returned by provider. A different decoder may be needed. Provider '
    'returned: b\\\'{"error":"invalid_grant","error_description":"Bad '
    'credentials"}\\\'\',)',)
<br>
Cannot connect to IRIDA, it is likely the base url in the configuration file is incorrect.

Also check that the IRIDA instance you are trying to connect to is running.

Alternatively, the client_id / client_secret may be incorrect

    ERROR    Can not connect to IRIDA
    ERROR    ERROR! Could not initialize irida api.
    ERROR    Errors: ('Could not connect to the IRIDA server. URL may be incorrect. IRIDA returned '
    'with error message: (MaxRetryError("HTTPConnectionPool(host=\'lcalhost\', '
    'port=8080): Max retries exceeded with url: /irida-latest/api/oauth/token '
    "(Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at "
    '0x7f2d3b6759b0>: Failed to establish a new connection: [Errno -2] Name or '
    'service not known\',))",),)',)
<br>
An invalid parser name was given, Double check your config file has a valid parser in the parser field

    AssertionError: Bad parser creation, invalid parser_type given: miseqa

## Unrecoverable Errors
In the case that an unrecoverable error occurs and uploader crashes, the error will be logged to `crash.log` in your default logging directory.
