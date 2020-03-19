from cerberus import Validator, TypeDefinition

from iridauploader.model.sample import Sample


class Project:

    # Define Sample as a type for validation
    _sample_type = TypeDefinition('sample', (Sample,), ())
    Validator.types_mapping['sample'] = _sample_type

    # schema for sequence file uploading
    uploadable_schema = {
        '_sample_list': {
            'type': 'list',
            'empty': False,  # must have at least 1 sample
            'schema': {'type': 'sample'}},
        '_name': {
            'type': 'string',
            'nullable': True,
            'required': False
        },
        '_description': {
            'type': 'string',
            'nullable': True,
            'required': False
        },
        '_id': {
            'type': 'string',
            'nullable': False,
            'required': True
        }
    }

    # schema for project uploading
    send_project_schema = {
        '_name': {
            'type': 'string',
            'nullable': False,
            'required': True,
            'minlength': 5  # when uploading a new project
        },
        '_description': {
            'type': 'string',
            'nullable': True,
            'required': False
        }
    }

    # project_id is optional because it's not necessary when creating a Project object to send.
    # project_id is the identifier key when getting projects from the API.
    def __init__(self, name=None, sample_list=None, description=None, id=None):
        self._name = name
        if sample_list is None:
            sample_list = []
        self._sample_list = sample_list
        self._description = str(description)
        self._id = str(id)

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def sample_list(self):
        return self._sample_list

    def add_sample(self, sample):
        self._sample_list.append(sample)

    @property
    def description(self):
        return self._description

    def get_uploadable_dict(self):  # formatting for sending to irida when creating a project
        return {"name": self._name,
                "projectDescription": self._description}

    def __str__(self):
        return "ID:" + self._id + " Name: " + self._name + " Description: " + self._description

    def get_dict(self):
        return self.__dict__
