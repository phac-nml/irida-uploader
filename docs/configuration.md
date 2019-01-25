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
* `parser` : Pick the parser that matches the file structure of your sequence files. We currently support [miseq](parsers/miseq.md) and [directory](parsers/directory.md).


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

### Linux:

Use the the `irida-uploader.sh` script included with the source code to upload.
