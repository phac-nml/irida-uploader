import unittest

from iridauploader.api import api_calls


class TestIsIridaVersionCompatible(unittest.TestCase):
    """
    Tests the api.api_calls._is_irida_version_compatible function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_simple_true(self):
        """
        Simple case
        :return:
        """
        result = api_calls.ApiCalls._is_irida_version_compatible(
            irida_version="23.01",
            minimum_irida_version="22.01"
        )
        self.assertTrue(result)

    def test_simple_false(self):
        """
        Simple case
        :return:
        """
        result = api_calls.ApiCalls._is_irida_version_compatible(
            irida_version="22.01",
            minimum_irida_version="23.01"
        )
        self.assertFalse(result)

    def test_simple_equal_true(self):
        """
        Simple case
        :return:
        """
        result = api_calls.ApiCalls._is_irida_version_compatible(
            irida_version="23.01",
            minimum_irida_version="23.01"
        )
        self.assertTrue(result)

    def test_unequal_length_true(self):
        """
        Simple case
        :return:
        """
        result = api_calls.ApiCalls._is_irida_version_compatible(
            irida_version="23.01.3",
            minimum_irida_version="22.01"
        )
        self.assertTrue(result)

    def test_unequal_length_false(self):
        """
        Simple case
        :return:
        """
        result = api_calls.ApiCalls._is_irida_version_compatible(
            irida_version="22.01.3",
            minimum_irida_version="23.01"
        )
        self.assertFalse(result)

    def test_simple_almost_equal_true(self):
        """
        Simple case
        :return:
        """
        result = api_calls.ApiCalls._is_irida_version_compatible(
            irida_version="23.01.2",
            minimum_irida_version="23.01.1"
        )
        self.assertTrue(result)

    def test_simple_almost_equal_false(self):
        """
        Simple case
        :return:
        """
        result = api_calls.ApiCalls._is_irida_version_compatible(
            irida_version="23.01.1",
            minimum_irida_version="23.01.2"
        )
        self.assertFalse(result)
