"""
A Sample will store (key: value) pairs using a dictionary.

Keys from a sequencer include: 'sampleName','description'

Keys from Irida will include these AND many others
"""
from cerberus import Validator, TypeDefinition
from copy import deepcopy

from .sequence_file import SequenceFile


class Sample:

    # Define SequenceFile as a type for validation
    _sample_type = TypeDefinition('sequence_file', (SequenceFile,), ())
    Validator.types_mapping['sequence_file'] = _sample_type

    uploadable_schema = {'_sequence_file': {
                            'type': 'sequence_file',
                            'nullable': False,
                            'required': True,
                         },
                         '_sample_name': {
                            'type': 'string',
                            'nullable': False,
                            'required': True,
                            'minlength': 3  # Minimum sample name length is 3
                         },
                         '_description': {
                            'type': 'string',
                            'nullable': True,
                            'required': False
                         },
                         '_sample_number': {
                            'anyof_type': ['string', 'integer'],
                            'nullable': True,
                            'required': False
                         }}

    def __init__(self, sample_name, description='', sample_number=None, samp_dict=None):
        self._sample_name = sample_name
        self._description = description
        self._sample_number = sample_number
        if samp_dict is None:
            samp_dict = {}
        self._sample_dict = dict(samp_dict)
        self._sequence_file = None

    @property
    def sample_name(self):
        return self._sample_name

    @property
    def description(self):
        return self._description

    @property
    def sample_number(self):
        return self._sample_number

    @property
    def sequence_file(self):
        return self._sequence_file

    @sequence_file.setter
    def sequence_file(self, sq):
        self._sequence_file = sq

    def get_irida_id(self):
        if "identifier" in self._sample_dict:
            return self.get("identifier")
        else:
            return None

    def get_uploadable_dict(self):  # formatting for sending to irida when creating a project
        uploadable_dict = deepcopy(self._sample_dict)
        uploadable_dict['sampleName'] = self.sample_name
        uploadable_dict['description'] = self.description
        return uploadable_dict

    def __getitem__(self, key):
        if key in self._sample_dict:
            return self._sample_dict[key]
        return None

    def get(self, key):
        return self.__getitem__(key)

    def __str__(self):
        return str(self.get_uploadable_dict) + str(self.sequence_file)

    def get_dict(self):
        return self.__dict__
