## Creating a new parser

Browsing through the `directory` and `miseq` parsers is the easiest way to get a feel for what is needed in a new parser, but below are explanations and information on what the hard requirements are.

### Create required files
Start by creating a new folder in `parser/`, for example `my-parser`

in `parser/my-parser` create your main python parser file `parser.py`

Create a `__init__.py` in `parser/my-parser` with the line:
```
from .parser import Parser
```
This is so the parser will be able to be grabbed by the `parser` module.

### Required functions for `parser.py`

####`get_required_file_list()` :

Returns a list of files that are required for a run directory to be considered valid.

For example, the `miseq` parser returns the following list, as the run cannot be uploaded without these files.
```
['SampleSheet.csv', 'CompletedJobInfo.xml']
```

####`find_runs(directory)` :

Given a directory, returns a list of `DirectoryStatus` objects for each directory in it.

This function should make use of `progress.get_directory_status(...)` to generate the DirectoryStatus objects.

This function should raise `exceptions.DirectoryError` if the directory is inaccessible.

####`find_single_run(directory)` :

Finds a run in the given directory. Returns a single `DirectoryStatus` object.

This function should raise `exceptions.DirectoryError` if the directory is inaccessible.

####`get_sample_sheet(directory)` :
Given a Directory, returns the path to the sample sheet or equivalent file.

This function should raise `exceptions.DirectoryError` when a directory is inaccessible, or if the sample sheet file is missing.


####`get_sequencing_run(sample_sheet)` :

Given the `sample_sheet` path, from the `get_sample_sheet` function, Creates a `SequencingRun` object with correct structure. [See Object Model Documentation](objects.md)

This function should make use of `exceptions.ValidationError` when errors occur so the user can be informed of problems with their sample sheet / samples.

`ValidationError` includes a `ValidationResult` object that can hold multiple errors. Include all errors encountered during parsing and building of the sequence run to give the user as much information as possible.

### Allow project to be grabbed by the uploader

Edit the file `parser/parser.py`

Edit the line
```
from . import directory, miseq
```
and add your new parser
```
from . import directory, miseq, my-parser
```

in the `factory(parser_type)` method, add your new parser to the `if` statements.

Now your parser will be able to be used when selected from the config file.
