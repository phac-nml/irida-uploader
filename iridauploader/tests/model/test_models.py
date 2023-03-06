"""
Test cases that check parts of the models that don't get validated through standard execution
"""

import unittest
import os
from unittest.mock import patch

from iridauploader import model

path_to_module = os.path.abspath(os.path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestProject(unittest.TestCase):
    """
    Tests for Project object
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_string_output(self):
        """
        Test the __str__ method
        """
        proj = model.Project("p1", None, "desc", 1)
        p_str = str(proj)
        self.assertEqual('ID:1 Name: p1 Description: desc', p_str)


class TestSample(unittest.TestCase):
    """
    Tests for Sample object
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_string_output(self):
        """
        Test the __str__ method
        """
        samp = model.Sample("s1", "desc", 1, None, 1)
        s_str = str(samp)
        self.assertEqual("{'sampleName': 's1', 'description': 'desc', 'sequenceFile': 'None'}", s_str)

    def test_get_dict(self):
        """
        test dictionary building
        """
        samp = model.Sample("s1", "desc", 1, None, 1)
        d = {'_description': 'desc',
             '_sample_dict': {},
             '_sample_id': 1,
             '_sample_name': 's1',
             '_sample_number': 1,
             '_sequence_file': None,
             '_skip': False}
        self.assertEqual(d, samp.get_dict())

    def test_get_sample_dict(self):
        """
        test metadata dictionary
        """
        samp = model.Sample(
            sample_name="s1",
            description="desc",
            sample_number=1,
            samp_dict={"some": "values", "are": "here"},
            sample_id=1
        )
        self.assertEqual({"some": "values", "are": "here"}, samp.sample_dict)

    def test_get_item_none(self):
        """
        test __getitem__ for item that doesn't exist
        """
        samp = model.Sample("s1", "desc", 1, None, 1)
        self.assertIsNone(samp.__getitem__("not a key"))


class TestSequenceFile(unittest.TestCase):
    """
    Tests for SequenceFile object
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_string_output(self):
        """
        Test the __str__ method
        """
        seq = model.SequenceFile(["file1", "file2"], {"some": "thing"})
        s_str = str(seq)
        self.assertEqual('{\'propertyDict\': "{\'some\': \'thing\'}", \'fileList\': "[\'file1\', ' '\'file2\']"}',
                         s_str)

    def test_get(self):
        """
        test get
        """
        seq = model.SequenceFile(["file1", "file2"], {"some": "thing"})
        self.assertEqual("thing", seq.get("some"))

    def test_get_item_none(self):
        """
        test get for item that doesn't exist
        """
        seq = model.SequenceFile(["file1", "file2"], {"some": "thing"})
        self.assertIsNone(seq.get("not a key"))

    def test_get_dict(self):
        """
        test dictionary building
        """
        seq = model.SequenceFile(["file1", "file2"], {"some": "thing"})
        d = {'_file_list': ['file1', 'file2'], '_properties_dict': {'some': 'thing'}}
        self.assertEqual(d, seq.get_dict())


class TestModelValidationError(unittest.TestCase):
    """
    Tests for ModelValidationError object
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_properties(self):
        """
        test properties
        """
        m = model.exceptions.ModelValidationError("msg", "this")
        self.assertEqual("this", m.object)
        self.assertEqual("msg", m.message)

    def test_string_output(self):
        """
        Test the __str__ method
        """
        m = model.exceptions.ModelValidationError("msg", None)
        m_str = str(m)
        self.assertEqual('msg', m_str)


class TestSequencingRun(unittest.TestCase):
    """
    Tests for SequencingRun object
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_properties(self):
        """
        test properties
        """
        s = model.SequencingRun({"some": "thing"}, [], "miseq")
        s.metadata = {"some", "where"}
        self.assertEqual({"some", "where"}, s.metadata)
        s.project_list = ["items", "here"]
        self.assertEqual(["items", "here"], s.project_list)
        s.sequencing_run_type = "miniseq"
        self.assertEqual("miniseq", s.sequencing_run_type)
