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
        self.assertEqual(p_str, 'ID:1 Name: p1 Description: desc')
