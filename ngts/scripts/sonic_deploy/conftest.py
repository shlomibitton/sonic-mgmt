"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest
import logging

logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest builtin
    """
    logger.info('Parsing deploy type')
    parser.addoption('--deploy_type', action='store', choices=['onie', 'sonic'], required=True, default='onie',
                     help='Deploy type')


@pytest.fixture(scope="module")
def deploy_type(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: setup name
    """
    return request.config.getoption('--deploy_type')
