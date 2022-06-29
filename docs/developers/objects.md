# Object Model

## Sequencing / IRIDA Objects

These objects are used to store the data of a sequencing run before uploading to IRIDA.

They each include a `uploadable_schema` which uses `cerberus` to define valid objects. Object validity is checked in `core/model_validator.py`, along with some extra edge case tests to ensure the built object model is ready for upload.

### SequencingRun `model/sequencing_run.py`

Each upload needs a single `SequencingRun` object that acts as the root for the tree of data.

It contains a `project_list` which relate to the IRIDA projects that samples will be uploaded to.

The `metadata` dict is mostly unused, but must include `layoutType` as either `PAIRED_END` or `SINGLE_END`, this determines if the samples within the sequencing run are paired end or single end reads.

There is also a helper method `is_paired_end` that checks against the `metadata` dict and returns a boolean.

### Project `model/project.py`

The `Project` object relates to a project on IRIDA.

The `id` field identifies what project number on IRIDA the samples are going to.

The `sample_list` list contains the `Sample` objects that will be uploaded.

When creating a new project on IRIDA using the API, a `name` at least 5 characters long must be given.

### Sample `model/sample.py`

The `Sample` object includes:

 * `name` : How the sample is identified on IRIDA
 * `description` : the description of the sample on IRIDA
 * `sample_id` : IRIDA identifier for the sample object
 * `sample_number` : a number used by some sequencers to denote (pre parsed) sample order
 * `sequence_file` : A `SequenceFile` object that holds the files to upload.
 * `sample_dict` : a meta data dictionary
 
### SequenceFile `model/sequence_file.py`

The `SeuqenceFile` holds the file paths to the sequence data to be uploaded.

It has a `file_list` list that can hold multiple files. Currently IRIDA only supports single end and paired end files (1 or 2 files) for upload.

It also includes a `properties_dict` that is used to store meta data, and is filled with required values by the API or Parsers before uploading.

### Metadata `model/metadata.py`

The `Metadata` object defines and stores additional metadata for upload to IRIDA in a key-value dictionary.

When using the API and the `send_metadata` method, a `Metadata` object must be passed to the method.

## Other Objects

### DirectoryStatus `model/directory_status.py`

`DirectoryStatus` objects contain a `directory`, a `status` and a `message`

The `progress` modules makes use of them.

These are used when deciding if a run has been uploaded, partially uploaded, is a new run, or is invalid.

The `directory` field holds the path to the directory of some potential sequencing run.

The `status` field can hold the following options, defined in the file. (e.g. DirectoryStatus.NEW)

* NEW
    * New runs, ready to upload
* INVALID
    * Used when a run directory does not have the base requirements to act as a run
    * This is never written to a status file, as reading a status file as invalid will not allow a run to be uploaded using the `--force` option. When a run cannot be uploaded, `ERROR` is instead written to file.
* PARTIAL
    * Parsing/Upload has started/partially completed for this run
* ERROR
    * Parsing/Upload has stopped because of some error.
* COMPLETE
    * Parsing/Upload has completed successfully

The `message` field is only filled if a run is `"invalid"`, and contains information on why a run is invalid.

### ValidationResult `model/validation_result.py`

`ValidationResult` objects contain an `error_list` with multiple errors. These are used to collect multiple `ModelValidationErrors` together so that all the validation issues can be seen at once.

## Exceptions

###ModelValidationError `model/exceptions/model_validation_result.py`

When validating the object model, A `ModelValidationError` will be thrown. It contains a `message` with information on the issue, and an `object` that holds the invalid object.