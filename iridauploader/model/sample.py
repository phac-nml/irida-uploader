"""
A Sample will store (key: value) pairs using a dictionary.

Keys from a sequencer include: 'sampleName','description'

Keys from Irida will include these AND many others
"""
from cerberus import Validator, TypeDefinition
from copy import deepcopy

from iridauploader.model.sequence_file import SequenceFile


class Sample:

    # Define SequenceFile as a type for validation
    _sample_type = TypeDefinition('sequence_file', (SequenceFile,), ())
    Validator.types_mapping['sequence_file'] = _sample_type

    uploadable_schema = {
        '_sequence_file': {
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
        },
        '_sample_id': {
            'type': 'integer',
            'nullable': True,
            'required': False
        },
        '_skip': {
            'type': 'boolean',
            'nullable': True,
            'required': False
        }
    }

    def __init__(self, sample_name, description='', sample_number=None, samp_dict=None, sample_id=None):
        """
        :param sample_name: string: displayed sample name on IRIDA
        :param description: string:
        :param sample_number: string or int: used during parsing step for some parsers that define their own numbers for samples
        :param samp_dict: dictionary of additional values
        :param sample_id: int: unique identifier defined by irida
        """
        self._sample_name = sample_name
        self._description = description
        self._sample_number = sample_number
        self._sample_id = sample_id
        if samp_dict is None:
            samp_dict = {}
        self._sample_dict = dict(samp_dict)
        self._sequence_file = None
        self._skip = False

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
    def sample_id(self):
        return self._sample_id

    @property
    def sequence_file(self):
        return self._sequence_file

    @sequence_file.setter
    def sequence_file(self, sq):
        self._sequence_file = sq

    @property
    def sample_dict(self):
        return self._sample_dict

    @property
    def skip(self):
        return self._skip

    @skip.setter
    def skip(self, skip):
        self._skip = skip

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
        d = self.get_uploadable_dict()
        d["sequenceFile"] = str(self.sequence_file)
        return str(d)

    def get_dict(self):
        return self.__dict__
