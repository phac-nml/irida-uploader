import argparse
import global_settings


class ConfigAction(argparse.Action):
    """
    This class is called when a config option is passed to via command line.

    It sets the global_settings config_file option to whatever was passed in the argument
    """
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        """
        Boilerplate for an argparse Action

        :param option_strings: A list of command-line option strings which
            should be associated with this action.
        :param dest: The name of the attribute to hold the created object(s)
        :param nargs: The number of command-line arguments that should be
            consumed. See argparse docs for details
        :param kwargs: All other options. See argparse docs for details
        """
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(ConfigAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Gets executed when the argument is included from the command line

        :param parser: Not used.
        :param namespace: Not used.
        :param values: The value passed via the command line. The global config_file variable will be set to this.
        :param option_string: not used
        :return: None
        """
        global_settings.config_file = values


# Set up an argument parser. We are using defaults to stay consistent with other software.
# description gets added to the usage statements
argument_parser = argparse.ArgumentParser(description='This program parses sequencing runs and uploads them to IRIDA.')
# Our main argument. It is required or else an error will be thrown when the program is run
argument_parser.add_argument('directory',
                             help='Location of sequencing run to upload')
# Optional argument, for using an alternative config file.
argument_parser.add_argument('-c', '--config',
                             action=ConfigAction,
                             help='Path to an alternative configuration file.'
                                  'This overrides the default config file in the config directory')


def main():
    # Parse the arguments passed from the command line and start the upload
    args = argument_parser.parse_args()
    upload(args.directory)


def upload(run_directory):
    # We import here instead of at the top so argparse can set the config files before the config module is imported
    from core import cli_entry
    cli_entry.validate_and_upload_single_entry(run_directory)


# This is called when the program is run for the first time
if __name__ == "__main__":
    main()
