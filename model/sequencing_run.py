from cerberus import Validator, TypeDefinition

from .project import Project


class SequencingRun:

    # Define Project as a type for validation
    _project_type = TypeDefinition('project', (Project,), ())
    Validator.types_mapping['project'] = _project_type

    uploadable_schema = {'_project_list': {
                            'type': 'list',
                            'empty': False,  # must have at least 1 project
                            'schema': {'type': 'project'}
                            },
                         '_metadata': {
                            'type': 'dict',
                            'schema': {'layoutType': {'type': 'string',
                                                      'required': True,
                                                      'allowed': ['PAIRED_END', 'SINGLE_END']}}
                         }}

    def __init__(self, metadata, project_list):
        self._project_list = project_list
        self._metadata = metadata

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

    def get_dict(self):
        return self.__dict__
