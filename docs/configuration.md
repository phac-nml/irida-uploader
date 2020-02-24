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
* `parser` : Pick the parser that matches the file structure of your sequence files. We currently support [miseq](parsers/miseq.md), [directory](parsers/directory.md) and [miniseq](parsers/miniseq.md).


###Example
```
[Settings]
client_id = uploader
client_secret = ZK1z6H165y4IZF2ckqNQES315OyKQU8CsrpHNdQr16
username = admin
password = password1
base_url = http://localhost:8080/irida-latest/api/
parser = miseq
```
This can also be found in the file `example_config.conf`

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

##Admin Option Multithreaded Upload

####Note: This is an experimental feature

The IRIDA Uploader can upload using multiple threads on the command line with the following option
```bash
--multithreading --threads 2
```
(more details in the `--help` command)

Multithreaded can also be configured system wide to be used in the GUI.

Because this is an experimental feature, no option is present in the GUI to enable multithreading and must be configured in the config file location as listed in an above section.

Add the following lines to the config file to enable multithreading.

```
multithreading = True
threads = 4
```

When using this feature, we recommend between 2 and 4 threads, with a maximum of 8 threads.

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
