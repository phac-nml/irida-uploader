import logging

from iridauploader.parsers import directory, miseq, miniseq, nextseq, nextseq2k_nml

supported_parsers = [
    'miseq',
    'miseq_v26',
    'miseq_v31',
    'miseq_win10_jun2021',
    'miniseq',
    'nextseq',
    'nextseq2k_nml',
    'iseq',
    'directory',
    'nanopore_assemblies',
    'seqfu',
]


def parser_factory(parser_type):
    """
    This factory creates and returns parser objects

    When creating a new parser, the parser type can be added here to enable it's usage.

    example:
        from parsers import parser_factory
        my_parser = parser_factory("directory")

    :param parser_type: a String of a valid parser name
    :return:
    """
    if parser_type in ['directory', 'nanopore_assemblies', 'seqfu']:
        logging.debug("Creating directory parser")
        return directory.Parser(parser_type_name=parser_type)
    if parser_type in ['miseq', 'miseq_v26']:
        logging.debug("Creating miseq (v26) parser")
        return miseq.Parser(parser_type_name=parser_type)
    if parser_type in ['miniseq', 'iseq', 'miseq_v31', 'miseq_win10_jun2021']:
        logging.debug("Creating miniseq/iseq/miseq_v31 parser")
        return miniseq.Parser(parser_type_name=parser_type)
    if parser_type == "nextseq":
        logging.debug("Creating nextseq parser")
        return nextseq.Parser(parser_type_name=parser_type)
    if parser_type == "nextseq_nml_classic":
        logging.debug("Creating nml custom nextseq parser")
        return nextseq.Parser(
            parser_type_name=parser_type,
            sample_sheet_override='SampleSheetClassic.csv'
        )
    if parser_type == "nextseq_nml_dual_upload":
        logging.debug("Creating nml custom nextseq parser with extra required files")
        return nextseq.Parser(
            parser_type_name=parser_type,
            additional_required_files=['RunMetadata.csv']
        )
    if parser_type == "nextseq_nml_strict_sample_name":
        logging.debug("Creating nml custom nextseq parser with strict sample name matching")
        return nextseq.Parser(
            parser_type_name=parser_type,
            strict_sample_name_matching=True
        )
    if parser_type == "nextseq2k_nml":
        logging.debug("Creating nextseq2k_nml parser")
        return nextseq2k_nml.Parser(parser_type_name=parser_type)
    raise AssertionError("Bad parser creation, invalid parser_type given: {}".format(parser_type))
