"""
Sample metadata can include:
samplePlate
sampleWell
i7IndexID
index
i5IndexID
index2
etc.
"""


class SequenceFile:

    uploadable_schema = {
        '_file_list': {
            'type': 'list',
            'empty': False,  # must have at least 1 file
            'nullable': False,
            'required': True,
            'schema': {'type': 'string'}
        },
        '_properties_dict': {'type': 'dict'}
    }

    def __init__(self, file_list, properties_dict=None):
        if properties_dict is None:
            self._properties_dict = {}
        else:
            self._properties_dict = properties_dict  # Sample metadata, needed run_id gets affixed in upload
        self._file_list = file_list

    @property
    def properties_dict(self):
        return self._properties_dict

    def get(self, key):
        ret_val = None
        if key in self._properties_dict:
            ret_val = self._properties_dict[key]
        return ret_val

    @property
    def file_list(self):
        return self._file_list

    def is_paired_end(self):
        return len(self._file_list) == 2

    def __str__(self):
        d = {'propertyDict': str(self._properties_dict), 'fileList': str(self._file_list)}
        return str(d)

    def get_dict(self):
        return self.__dict__
