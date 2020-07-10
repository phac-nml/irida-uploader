class OtherMetadata:

    def __init__(self, metadata=None):
        if metadata is None:
            metadata = {}
        self._metadata = metadata

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    def add_metadata_entry(self, key, value):
        self._metadata[key] = value

    def get_uploadable_dict(self):
        uploadable_dict = {}
        for key, value in self._metadata.items():
            uploadable_dict[key] = {"type": "text", "value": "{}".format(value)}
        return uploadable_dict
