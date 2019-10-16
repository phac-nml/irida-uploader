import logging

from . import directory, miseq, miniseq, nextseq

supported_parsers = [
    'miseq',
    'miniseq',
    'nextseq',
    'iseq',
    'directory',
]


class Parser:
    """
    This class handles creation of the different parser objects.

    When creating a new parser, the parser type can be added here to enable it's usage.

    Like the miseq and directory parser, a new parser class needs the following static methods
        find_single_run(directory)
        find_runs(directory)
        get_required_file_list()
        get_sample_sheet(directory)
        get_sequencing_run(sample_sheet)

    """

    @staticmethod
    def factory(parser_type):
        """
        This factory creates and returns parser objects

        example:
            from parser import Parser
            my_parser = Parser.factory("directory")

        :param parser_type: a String of a valid parser name
        :return:
        """
        if parser_type == "directory":
            logging.debug("Creating directory parser")
            return directory.Parser()
        if parser_type == "miseq":
            logging.debug("Creating miseq parser")
            return miseq.Parser()
        if parser_type == "miniseq" or parser_type == "iseq":
            logging.debug("Creating miniseq/iseq parser")
            return miniseq.Parser()
        if parser_type == "nextseq":
            logging.debug("Creating nextseq parser")
            return nextseq.Parser()
        raise AssertionError("Bad parser creation, invalid parser_type given: {}".format(parser_type))
