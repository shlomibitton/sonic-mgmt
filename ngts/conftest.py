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
from ngts.tools.skip_test.skip import ngts_skip
from distutils.dist import strtobool
from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
logger = logging.getLogger()

pytest_plugins = ('ngts.tools.sysdumps', 'ngts.tools.loganalyzer')


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


@pytest.fixture(scope='session')
def show_platform_summary(topology_obj):
    return topology_obj.players['dut']['engine'].run_cmd('show platform summary')


@pytest.fixture(autouse=True)
def skip_test_according_to_ngts_skip(request, show_platform_summary):
    """
    This fixture doing skip for test cases according to BUG ID in Redmine/GitHub or platform
    :param request: pytest buildin
    :param show_platform_summary: output for cmd 'show platform summary' from fixture show_platform_summary
    """
    skip_marker = 'ngts_skip'
    if request.node.get_closest_marker(skip_marker):
        rm_ticket_list = request.node.get_closest_marker(skip_marker).args[0].get('rm_ticket_list')
        github_ticket_list = request.node.get_closest_marker(skip_marker).args[0].get('github_ticket_list')
        platform_prefix_list = request.node.get_closest_marker(skip_marker).args[0].get('platform_prefix_list')
        operand = request.node.get_closest_marker(skip_marker).args[0].get('operand', 'or')

        ngts_skip(show_platform_summary, rm_ticket_list, github_ticket_list, platform_prefix_list, operand)


def pytest_runtest_setup(item):
    """
    Pytest hook - see https://docs.pytest.org/en/stable/reference.html#pytest.hookspec.pytest_runtest_setup
    """
    ngts_skip_test_change_fixture_execution_order(item)


def ngts_skip_test_change_fixture_execution_order(item):
    """
    The purpose of this method is to change the order of fixtures execution - skip test by ngts logic should be run first
    Otherwise autouse fixtures of ignored tests will be running, even if the test case is skipped.
    :param item: pytest buildin
    """
    ngts_skip_fixture = item.fixturenames.pop(item.fixturenames.index('skip_test_according_to_ngts_skip'))
    if ngts_skip_fixture:
        item.fixturenames.insert(0, ngts_skip_fixture)


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook which are executed after all tests before exist from program
    :param session: pytest buildin
    :param exitstatus: pytest buildin
    """
    if not session.config.getoption("--collectonly"):
        allure_server_ip = '10.215.11.120'
        allure_server_port = '5050'
        allure_report_dir = session.config.known_args_namespace.allure_report_dir
        AllureServer(allure_server_ip, allure_server_port, allure_report_dir).generate_allure_report()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook which are executed in all phases: Setup, Call, Teardown
    :param item: pytest buildin
    :param call: pytest buildin
    """
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope='session')
def ha_dut_1_mac(topology_obj):
    """
    Pytest fixture which are returning mac address for link: ha-dut-1
    :param topology_obj: topology object fixture
    """
    ha_dut_1 = topology_obj.ports['ha-dut-1']
    ha_engine = topology_obj.players['ha']['engine']
    return LinuxMacCli.get_mac_address_for_interface(ha_engine, ha_dut_1)


@pytest.fixture(scope='session')
def ha_dut_2_mac(topology_obj):
    """
    Pytest fixture which are returning mac address for link: ha-dut-2
    :param topology_obj: topology object fixture
    """
    ha_dut_2 = topology_obj.ports['ha-dut-2']
    ha_engine = topology_obj.players['ha']['engine']
    return LinuxMacCli.get_mac_address_for_interface(ha_engine, ha_dut_2)


@pytest.fixture(scope='session')
def hb_dut_1_mac(topology_obj):
    """
    Pytest fixture which are returning mac address for link: hb-dut-1
    :param topology_obj: topology object fixture
    """
    hb_dut_1 = topology_obj.ports['hb-dut-1']
    hb_engine = topology_obj.players['hb']['engine']
    return LinuxMacCli.get_mac_address_for_interface(hb_engine, hb_dut_1)


@pytest.fixture(scope='session')
def hb_dut_2_mac(topology_obj):
    """
    Pytest fixture which are returning mac address for link: hb-dut-2
    :param topology_obj: topology object fixture
    """
    hb_dut_2 = topology_obj.ports['hb-dut-2']
    hb_engine = topology_obj.players['hb']['engine']
    return LinuxMacCli.get_mac_address_for_interface(hb_engine, hb_dut_2)
