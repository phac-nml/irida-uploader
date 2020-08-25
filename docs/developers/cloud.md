
# Deploying the uploader to the cloud

While there is not an end to end solution that you can deploy onto the cloud, the iridauploader does allow you to use it's modules to simplify your code for cloud deployment.


#### Why can't I just deploy straight to cloud?

The main difficulty is that each cloud storage solution maintains files differently, and it would not be feasible for us to support every cloud environment available.

## How to Deploy to cloud

The simplest way is to incorperate the `iridauploader` modules from `pip` / `PyPi` .

`pip install iridauploader`

Example for creating a new instance of the API, and a MiSeq Parser:

```python
import iridauploader.api as api
import iridauploader.parsers as parsers

api_instance = api.ApiCalls(client_id, client_secret, base_url, username, password, max_wait_time)
parser_instance = parsers.parser_factory("miseq")
```

## Examples for deployment on Azure Cloud

In these examples we have the following setup:
* We are using an Azure Function App using Python
* Files are stored in blob storage containers (in our example `myblobcontainer`)
* We use a BlobTrigger to run when a new run is uploaded with the path identifier `myblobcontainer/{name}.csv`

Example `function.json` file:

```json
{
  "scriptFile": "__init__.py",
  "disabled": false,
  "bindings": [
      {
          "name": "myblob",
          "type": "blobTrigger",
          "direction": "in",
          "path": "myblobcontainer/{name}.csv",
          "connection":"AzureWebJobsStorage"
      }
  ]
}
```

For the following example, we have this simple setup at the top of our `__init__.py` function app file.

```python
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient
from azure.storage.blob import ContainerClient
import azure.functions as func

from iridauploader import parsers


# connect to our blob storage
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
# These strings could be fetched somehow, but this works for an example
container_name = "myblobcontainer"
container_client = blob_service_client.get_container_client(container_name)
```

### Miseq example

For this example, we will be getting the entire folder for a miseq run, as a set of blobs. When parsing directly from other sequencers, please consult the parser documentation for file structure differences.

```python
def main(myblob: func.InputStream):
    logging.info('Python blob trigger function %s', myblob.name)

    # download the sample sheet so it can be parsed
    download_sample_sheet_file_path = os.path.join(local_path, local_file_name)
    with open(download_sample_sheet_file_path, "wb") as download_file:
        download_file.write(myblob.read())
    logging.info("done downloading")

    # get run directory (getting the middle portion)
    # example 'myblobcontainer/miseq_run/SampleSheet.csv' -> 'miseq_run
    run_directory_name = posixpath.split(posixpath.split(myblob.name)[0])[1]

    # we are gonna use miseq for this example
    my_parser = parsers.parser_factory("miseq")
    logging.info("built parser")

    # This example was tested locally on a windows machine, so replacing \\ with / was needed for compatibility
    relative_data_path = my_parser.get_relative_data_directory().replace("\\", "/")
    full_data_dir = posixpath.join(
        run_directory_name, 
        relative_data_path)

    # list the blobs of the run directory
    blob_list = list(container_client.list_blobs(full_data_dir))
    file_list = []
    # The file_blob_tuple_list could be useful when moving to the uploading stage in the case where
    # you do not want to use the iridauploader.api module to upload to irida, otherwise it can be ignored
    file_blob_tuple_list = []
    for file_blob in blob_list:
        file_name = remove_prefix(file_blob.name, full_data_dir)
        file_list.append(file_name)
        file_blob_tuple_list.append({"file_name": file_name, "blob": file_blob})

    # TODO, put a try catch around this with the parser exceptions.
    # We can catch errors within the samplesheet or missing files here
    sequencing_run = my_parser.get_sequencing_run(
        sample_sheet=download_sample_sheet_file_path, 
        run_data_directory=full_data_dir, 
        run_data_directory_file_list=file_list)
    logging.info("built sequencing run")

    # move to upload / error handling when the parser finds an error in the run


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    raise Exception("should not happen")
```

### Directory example

In this example we will be using the basic file layout for a directory upload.

```
.directory_run
├── file_1.fastq.gz
├── file_2.fastq.gz
└── SampleList.csv
```

```python
def main(myblob: func.InputStream):
    logging.info('Python blob trigger function %s', myblob.name)

    # download the sample sheet
    download_sample_sheet_file_path = os.path.join(local_path, local_file_name)
    with open(download_sample_sheet_file_path, "wb") as download_file:
        download_file.write(myblob.read())
    logging.info("done downloading")

    # get run directory (getting the middle portion)
    # example 'myblobcontainer/directory_run/SampleSheet.csv' -> 'directory_run
    run_directory_name = posixpath.split(posixpath.split(myblob.name)[0])[1]

    # we are gonna use directory for this example
    my_parser = parsers.parser_factory("directory")
    logging.info("built parser")

    # list the blobs of the run directory
    blob_list = list(container_client.list_blobs(run_directory_name))
    file_list = []
    # The file_blob_tuple_list could be useful when moving to the uploading stage in the case where
    # you do not want to use the iridauploader.api module to upload to irida, otherwise it can be ignored
    file_blob_tuple_list = []
    for file_blob in blob_list:
        file_name = remove_prefix(file_blob.name, run_directory_name)
        # trim the leading 
        file_name = file_name.replace("/","")
        file_list.append(file_name)
        file_blob_tuple_list.append({"file_name": file_name, "blob": file_blob})

    # TODO, put a try catch around this with the parser exceptions.
    # We can catch errors within the samplesheet or missing files here
    sequencing_run = my_parser.get_sequencing_run(
        sample_sheet=download_sample_sheet_file_path, 
        run_data_directory_file_list=file_list)
    logging.info("built sequencing run")

    # move to upload / error handling when the parser finds an error in the run
    

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    raise Exception("should not happen")
```
