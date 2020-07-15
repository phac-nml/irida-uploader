import logging
import os

import iridauploader.progress as progress
import iridauploader.model as model

from iridauploader.parsers import exceptions
from iridauploader.parsers import common
from iridauploader.parsers.directory import sample_parser, validation


class Parser:

    @staticmethod
    def get_metadata_list(metadata_file):

        csv_reader = common.get_csv_reader(metadata_file)

        # todo all this, a bit to complex for after 5pm

        # todo gotta throw validation errors if things go wrong

        for line in csv_reader:
            if first_line:

                first_line = False

