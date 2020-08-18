class BaseParser:
    """
     This class is the abstract for the different parser objects.

     Like the miseq and directory parser, a new parser class needs the following static methods
         find_single_run(directory)
         find_runs(directory)
         get_required_file_list()
         get_sample_sheet(directory)
         get_sequencing_run(sample_sheet, ...)

     """
    def __init__(self, parser_type_name, required_file_list):
        """
        Base Parser initialization
        :param parser_type_name: string: used as the run type identifier when creating the sequence run
        :param required_file_list: [file_names]
        """
        self._parser_type_name = parser_type_name
        self._required_file_list = required_file_list

    def get_required_file_list(self):
        """
        Returns a list of files that are required for a run directory to be considered valid
        :return: [files_names]
        """
        return self._required_file_list

    def get_parser_type_name(self):
        """
        Returns the parser type name, used when generating the api route to determine sequencer type
        :return:
        """
        return self._parser_type_name
