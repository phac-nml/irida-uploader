def send_message(message):
    """
    This will eventually handle the message passing from the api layer
    Right now it is just a dummy function that prints
    """
    print(message)
    return


"""
Below is work in progress (non working) code of how the code could flow
to be redone once the UI is implemented
"""

#
# class MessageTopics(object):
#     upload_progress_topic = "finished_run_scan"
#     upload_started_topic = "run_discovered"
#     upload_completed_topic = "garbled_sample_sheet"
#     upload_failed_topic = "missing_files"
#
#
# class ApiMessage(object):
#     # todo: add run_id to this too?
#     def __init__(self,
#                  topic,
#                  exception=None,
#                  project_id=None,
#                  sample_name=None,
#                  sequence_file_name=None,
#                  progress=None):
#         self._topic = topic
#         self._exception = exception
#         self._project_id = project_id
#         self._sample_name = sample_name
#         self._sequence_file_name = sequence_file_name
#         self._progress = progress
#
#     @property
#     def property(self):
#         return self._topic
#
#     @property
#     def exception(self):
#         return self._exception
#
#     @property
#     def project_id(self):
#         return self._project_id
#
#     @property
#     def sample_name(self):
#         return self._sample_name
#
#     @property
#     def sequence_file_name(self):
#         return self._sequence_file_name
#
#     @property
#     def progress(self):
#         return self._progress
#
#     def __str__(self):
#         return "topic: " + self._topic + \
#                ", project_id: " + self.project_id + \
#                ", sample_name: " + self._sample_name + \
#                ", sequence_file_name: " + self._sequence_file_name
