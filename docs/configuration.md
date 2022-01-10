## Configuration

To use the IRIDA uploader, you will need to create a client in IRIDA for the uploader.

Please refer to the ["Configure the Uploader" section on the IRIDA tutorials](https://irida.corefacility.ca/documentation/user/tutorials/uploader-tool/) for more information.

###File Location

You can create the config file yourself, or simply run the uploader for the first time to create a new config file with empty/default values.

You can find this file:

Linux: `~/.config/irida-uploader/config.conf`

Windows: `C:\Users\<Username>\AppData\Local\irida-uploader\config.conf`

###Options

The config file has the following fields:

* `client_id` : The id from the IRIDA client you created
* `client_secret` : The secret from the IRIDA client you created
* `username` : The user that will be accessing projects/samples, this user needs the `Sequencer` or `Administrator` role. 
* `password` : Corresponding password for above user.
* `base_url` : The server URL is the location that the uploader should upload data to. If you navigate to your instance of IRIDA in your web browser, the URL (after you’ve logged in) will often look like: `https://irida.corefacility.ca/irida/`. The URL you should enter into the Server URL field is that URL, with `api/` at the end. So in the case of `https://irida.corefacility.ca/irida/`, you should enter the URL `https://irida.corefacility.ca/irida/api/`
* `parser` : Pick the parser that matches the file structure of your sequence files. We currently support [miseq v26](parsers/miseq_v26.md), [miseq v31](parsers/miseq_v31.md), [nextseq](parsers/nextseq.md), [nextseq2k](parsers/nextseq2k_nml.md), [basic directory](parsers/directory.md), [SeqFu](parsers/directory.md) and [miniseq](parsers/miniseq.md).
* `readonly` : When set to True, uploader will not write any files to sequencing run directory, meaning upload progress / status and logs will not be generated in the sequencing run directory.
* `delay` : Can be given a Integer to delay a run from uploading when discovered for a number of minutes. When automating batch upload jobs on windows, we recommend this delay be at least 60 minutes.
* `timeout` : Accepts an Integer for the expected transfer time in seconds per MB. Default is 10 second for every MB of data to transfer. Increasing this number can help reduce timeout errors in cases where connection speed is very slow.
* `minimum_file_size` : Accepts an Integer for the minimum file size in KB. Default is 0 KB. Files that are too small will appear as an error during run validation.
###Example
```
[Settings]
client_id = uploader
client_secret = ZK1z6H165y4IZF2ckqNQES315OyKQU8CsrpHNdQr16
username = admin
password = password1
base_url = http://localhost:8080/irida-latest/api/
parser = miseq
readonly = False
delay = 0
timeout = 10
minimum_file_size = 0
```
This can also be found in the file `examples/example_config.conf`

## Specify other config file

Alternatively, you can pass a config file to the command line uploader as an optional argument.

Use `-c` or `--config` and specify the path to your config file.

Example:

```
# Linux
  $ ./irida-uploader.sh --config /path/to/config.conf /path/to/the/sequencing/run/

# Windows
  C:\Users\username> iridauploader --config \path\to\config.conf \path\to\my\samples\
```

## Override config options in file

You can override one or more config options with their respective command line arguments

This can be done as given parameters `--option parameter` or via user prompt `--option`

```bash
  -ci [CONFIG_CLIENT_ID], --config_client_id [CONFIG_CLIENT_ID]
                        Override "client_id" in config file. Can be used
                        without a parameter to prompt for input.
  -cs [CONFIG_CLIENT_SECRET], --config_client_secret [CONFIG_CLIENT_SECRET]
                        Override "client_secret" in config file. Can be used
                        without a parameter to prompt for input.
  -cu [CONFIG_USERNAME], --config_username [CONFIG_USERNAME]
                        Override "username" in config file. Can be used
                        without a parameter to prompt for input.
  -cp [CONFIG_PASSWORD], --config_password [CONFIG_PASSWORD]
                        Override "password" in config file. Can be used
                        without a parameter to prompt for input.
  -cb [CONFIG_BASE_URL], --config_base_url [CONFIG_BASE_URL]
                        Override "base_url" in config file. Can be used
                        without a parameter to prompt for input.
  -cr [CONFIG_PARSER], --config_parser [CONFIG_PARSER]
                        Override "parser" in config file. Can be used without
                        a parameter to prompt for input.
```

###Admin Config Override

In some workflows it makes sense to have a single irida user account uploading for any user signed in on the sequencer machine. In this case the config override can be used to avoid having to enter the credentials for each new user.

You can add your config file to the source code directory and the uploader will prioritize it over the default user config file.

Note: Specifying the config file with the `--config` option takes priority over the override config file.

#### Windows file location

First, when installing the uploader, make sure to install for all users.

The config file can be placed in the install directories `pkgs` folder. The default is:

`C:\Program Files (x86)\IRIDA Sequence Uploader GUI\pkgs`

#### Linux file location

The config file can be placed into the root directory of the source code: `irida-uploader/`
