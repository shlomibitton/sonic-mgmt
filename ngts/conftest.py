"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest
import logging

from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name
from ngts.cli_wrappers.sonic.sonic_cli import SonicCli
from ngts.cli_wrappers.linux.linux_cli import LinuxCli
from ngts.tools.allure_report.allure_server import AllureServer
from distutils.dist import strtobool
logger = logging.getLogger()


@pytest.fixture(scope='session')
def is_simx(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: setup name
    """
    return strtobool(request.config.getoption('--simx'))


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest buildin
    """
    logger.info('Parsing pytest options')
    parser.addoption('--setup_name', action='store', required=True, default=None,
                     help='Setup name, example: sonic_tigris_r-tigris-06')
    logger.info("Parsing if simx setup")
    parser.addoption('--simx', default="False", help='value indicating if the setup is a simx setup')


@pytest.fixture(scope='session')
def setup_name(request):
    """
    Method for get setup name from pytest arguments
    :param request: pytest buildin
    :return: setup name
    """
    return request.config.getoption('--setup_name')


@pytest.fixture(scope='session', autouse=True)
def topology_obj(setup_name):
    """
    Fixture which create topology object before run tests and doing cleanup for ssh engines after test executed
    :param setup_name: example: sonic_tigris_r-tigris-06
    """
    logger.debug('Creating topology object')
    topology = get_topology_by_setup_name(setup_name, slow_cli=False)
    update_topology_with_cli_class(topology)
    yield topology
    logger.debug('Cleaning-up the topology object')
    for player_name, player_attributes in topology.players.items():
        player_attributes['engine'].disconnect()


def update_topology_with_cli_class(topology):
    # TODO: determine player type by topology attribute, rather than alias
    for player_key, player_info in topology.players.items():
        if player_key == 'dut':
            player_info['cli'] = SonicCli()
        else:
            player_info['cli'] = LinuxCli()


@pytest.fixture(scope='session', autouse=True)
def current_platform(topology_obj):
    return topology_obj.players['dut']['engine'].run_cmd('show platform summary')


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook which are executed after all tests before exist from program
    :param session: pytest buildin
    :param exitstatus: pytest buildin
    """
    allure_server_ip = '10.215.11.120'
    allure_server_port = '5050'
    allure_report_dir = session.config.known_args_namespace.allure_report_dir
    AllureServer(allure_server_ip, allure_server_port, allure_report_dir).generate_allure_report()
