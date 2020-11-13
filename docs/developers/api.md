# The `api` Module

The `api` module is essentially a python wrapper for the [IRIDA REST API](https://irida.corefacility.ca/documentation/developer/rest/).

It is used in the IRIDA uploader to handle interaction between the uploader logic and IRIDA, but the module can be used on it's own to interact with IRIDA.

## Setup

The module can be used as follows:

```python
# import the module
from iridauploader import api

# Create an api instance by initializing an ApiCalls object
api_instance = api.ApiCalls(client_id, client_secret, base_url, username, password, timeout_multiplier)
```

For more information on the arguments passed to `ApiCalls`, please see the [configuration documentation](../configuration.md)

## Use

### Getting Data from IRIDA

#### get_projects(self)
API call to api/projects to get list of projects

**returns:**

List containing projects. each project is Project object.

#### get_samples(self, project_id)
API call to api/projects/project_id/samples

**arguments:**

project_id -- project identifier from irida

**returns:**

list of samples for the given project.
Each sample is a Sample object.

#### get_sequence_files(self, project_id, sample_name)
API call to api/projects/project_id/sample_id/sequenceFiles
We fetch the sample file through the project id on this route

**arguments:**

sample_name -- the sample name identifier to get from irida, relative to a project
project_id -- the id of the project the sample is on

**returns:**

list of sequencefile dictionary for given sample_id

#### get_assemblies_files(self, project_id, sample_name)
API call to api/projects/project_id/sample_id/assemblies
We fetch the assemblies files through the project id on this route

**arguments:**

sample_name -- the sample name identifier to get from irida, relative to a project
project_id -- the id of the project the sample is on

**returns:**

returns list of assemblies files dictionary for given sample_id

### get_fast5_files(self, project_id, sample_name)
API call to api/projects/project_id/sample_id/sequenceFiles/fast5
We fetch the fast5 files through the project id on this route

**arguments:**

sample_name -- the sample name identifier to get from irida, relative to a project
project_id -- the id of the project the sample is on

**returns:**

returns list of fast5 files dictionary for given sample_id

#### get_metadata(self, sample_name, project_id)
API call to api/samples/sample_id/metadata
We fetch the other metadata metrics through the sample name and its id from the project

**arguments:**

sample_id -- the sample number identifier to get from irida
project_id -- the id of the project the sample is on

**returns:**

returns dictionary of metadata for the given sample_id

### Sending Data to IRIDA

#### send_project(self, project, clear_cache=True)
post request to send a project to IRIDA via API
the project being sent requires a name that is at least
5 characters long

**arguments:**

project -- a Project object to be sent.

**returns:**

A dictionary containing the result of post request.
when post is successful the dictionary it returns will contain the same
name and projectDescription that was originally sent as well as
additional keys like createdDate and identifier.
when post fails then an error will be raised so return statement is
not even reached.

#### send_sample(self, sample, project_id)
Post request to send a sample to a project

**arguments:**

sample -- Sample object to send
project_id -- id of project to send sample too

**returns:**

Unmodified json response from server

#### send_sequence_files(self, sequence_file, sample_name, project_id, upload_id, upload_mode=MODE_DEFAULT)
Post request to send sequence files found in given sample argument
raises error if either project ID or sample ID found in Sample object
doesn't exist in irida

**arguments:**

sequence_file -- SequenceFile object to send

sample_name -- irida sample name identifier to send to

project_id -- irida project identifier

upload_id -- the run to upload the files to

upload_mode -- default:MODE_DEFAULT -- which upload mode will be used

**returns:**

unmodified json response from server.

#### send_metadata(self, metadata, project_id, sample_name)
Put request to add user metadata to specific sample name in the project.
Raises error if either project ID or sample name found in Sample object
doesn't exist in irida

**arguments:**

metadata -- Metadata object to send to irida

project_id -- irida project identifier

sample_name -- sample name found in specified irida project

**returns:**

unmodified json response from server.

### Getting / Creating / Modifying Sequencing Runs

#### get_seq_runs(self)
Get list of all SequencingRun objects

**returns:**

list of SequencingRuns

#### create_seq_run(self, metadata)
Create a sequencing run.

uploadStatus "UPLOADING"

There are some parsed metadata keys from the SampleSheet.csv that are
currently not accepted/used by the API so they are discarded.
Everything not in the acceptable_properties list below is discarded.

**arguments:**

metadata -- SequencingRun's metadata

**returns:**

the sequencing run identifier for the sequencing run that was created

#### set_seq_run_complete(self, identifier)
Update a sequencing run's upload status to "COMPLETE"

**arguments:**

identifier -- the id of the sequencing run to be updated

**returns:**

unmodified json response from server

#### set_seq_run_uploading(self, identifier)
Update a sequencing run's upload status to "UPLOADING"

**arguments:**

identifier -- the id of the sequencing run to be updated

**returns:**

unmodified json response from server

#### set_seq_run_error(self, identifier)
Update a sequencing run's upload status to "ERROR"

**arguments:**

identifier -- the id of the sequencing run to be updated

**returns:**

unmodified json response from server


### Querying IRIDA

#### project_exists(self, project_id)
Check if a sample exists on a project

**arguments:**

project_id -- project that we are checking for existence
**returns:**

True or False

#### sample_exists(self, sample_name, project_id)
Check if a sample exists on a project

**arguments:**

sample_name -- sample to confirm existence of
project_id -- project that we think the sample is on

**returns:**

True or False
