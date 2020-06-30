from cerberus import Validator, TypeDefinition

from iridauploader.model.project import Project


class SequencingRun:

    # Define Project as a type for validation
    _project_type = TypeDefinition('project', (Project,), ())
    Validator.types_mapping['project'] = _project_type

    uploadable_schema = {
        '_project_list': {
            'type': 'list',
            'empty': False,  # must have at least 1 project
            'schema': {'type': 'project'}
        },
        '_metadata': {
            'type': 'dict',
            'schema': {
                'layoutType': {
                    'type': 'string',
                    'required': True,
                    'allowed': ['PAIRED_END', 'SINGLE_END']
                }
            }
        },
        '_assemblies': {
            'type': 'boolean',
            'required': True
        },
        '_sequencing_run_type': {
            'type': 'string',
            'required': True
        }
    }

    def __init__(self, metadata, project_list, sequencing_run_type, assemblies=False):
        self._project_list = project_list
        self._metadata = metadata
        self._assemblies = assemblies
        self._sequencing_run_type = sequencing_run_type

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata_dict):
        self._metadata = metadata_dict

    @property
    def project_list(self):
        return self._project_list

    @project_list.setter
    def project_list(self, p_list):
        self._project_list = p_list

    @property
    def sequencing_run_type(self):
        return self._sequencing_run_type

    @sequencing_run_type.setter
    def upload_route_string(self, sequencing_run_type):
        self._sequencing_run_type = sequencing_run_type

    @property
    def assemblies(self):
        return self._assemblies

    @assemblies.setter
    def assemblies(self, assemblies):
        self._assemblies = assemblies

    def get_dict(self):
        return self.__dict__
