import pytest

def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true", help="Run the (longer running) integration tests.")
    parser.addoption("--irida-version", action="store", default="master", help="The version of IRIDA to check out for the integration tests.")
