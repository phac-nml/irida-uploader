"""
Metadata defines and stores metadata in (key: value) pairs using a dictionary

(key: value) pairs can take any string so long as they are structured as such:
    { "Key_1": "Value_1", "Key_2": "Value_2" ... }
"""


class Metadata:

    def __init__(self, metadata=None, project_id=None, sample_name=None):
        if metadata is None:
            metadata = {}
        self._metadata = metadata
        self._project_id = project_id
        self._sample_name = sample_name

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    @property
    def project_id(self):
        return self._project_id

    @project_id.setter
    def project_id(self, project_id):
        self._project_id = project_id

    @property
    def sample_name(self):
        return self._sample_name

    @sample_name.setter
    def sample_name(self, sample_name):
        self._sample_name = sample_name

    def add_metadata_entry(self, key, value):
        self._metadata[key] = value

    def get_uploadable_dict(self):
        uploadable_dict = {}
        for key, value in self._metadata.items():
            uploadable_dict[key] = {"type": "text", "value": "{}".format(value)}
        return uploadable_dict
