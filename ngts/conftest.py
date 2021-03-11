"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest
import logging
import re
from dotted_dict import DottedDict

from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name
from ngts.cli_wrappers.sonic.sonic_cli import SonicCli
from ngts.cli_wrappers.linux.linux_cli import LinuxCli
from ngts.tools.allure_report.allure_server import AllureServer
from ngts.tools.skip_test.skip import ngts_skip
from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
logger = logging.getLogger()

pytest_plugins = ('ngts.tools.sysdumps', 'ngts.tools.loganalyzer', 'pytester')


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest buildin
    """
    logger.info('Parsing pytest options')
    parser.addoption('--setup_name', action='store', required=True, default=None,
                     help='Setup name, example: sonic_tigris_r-tigris-06')
    parser.addoption('--base_version', action='store', default=None, help='Path to base SONiC version')
    parser.addoption('--target_version', action='store', default=None, help='Path to target SONiC version')
    parser.addoption('--wjh_deb_url', action='store', default=None, help='URL path to WJH deb package')


@pytest.fixture(scope="session")
def base_version(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: base_version argument value
    """
    return request.config.getoption('--base_version')


@pytest.fixture(scope="session")
def target_version(request):
    """
    Method for getting target version from pytest arguments
    :param request: pytest builtin
    :return: target_version argument value
    """
    return request.config.getoption('--target_version')


@pytest.fixture(scope="session")
def wjh_deb_url(request):
    """
    Method for getting what-just-happend deb file URL from pytest arguments
    :param request: pytest builtin
    :return: wjh_deb_url argument value
    """
    return request.config.getoption('--wjh_deb_url')


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
def ha_dut_1_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: ha-dut-1
    """
    return LinuxMacCli.get_mac_address_for_interface(engines.ha, interfaces.ha_dut_1)


@pytest.fixture(scope='session')
def ha_dut_2_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: ha-dut-2
    """
    return LinuxMacCli.get_mac_address_for_interface(engines.ha, interfaces.ha_dut_2)


@pytest.fixture(scope='session')
def hb_dut_1_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: hb-dut-1
    """
    return LinuxMacCli.get_mac_address_for_interface(engines.hb, interfaces.hb_dut_1)


@pytest.fixture(scope='session')
def hb_dut_2_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: hb-dut-2
    """
    return LinuxMacCli.get_mac_address_for_interface(engines.hb, interfaces.hb_dut_2)


@pytest.fixture(scope='session')
def hwsku(show_platform_summary):
    """
    Pytest fixture which are returning hwsku
    :param show_platform_summary: show_platform_summary fixture
    """
    hwsku = re.search(r'HwSKU:\s(.*)', show_platform_summary, re.IGNORECASE).group(1)
    return hwsku


@pytest.fixture(scope='session')
def platform(show_platform_summary):
    """
    Pytest fixture which are returning platform
    :param show_platform_summary: show_platform_summary fixture
    """
    platform = re.search(r'Platform:\s*(.*)', show_platform_summary, re.IGNORECASE).group(1)
    return platform


@pytest.fixture(scope='session')
def sonic_version(engines):
    """
    Pytest fixture which are returning current SONiC installed version
    :param engines: dictionary with available engines
    :return: string with current SONiC version
    """
    show_version_output = engines.dut.run_cmd('sudo show version')
    sonic_ver = re.search(r'SONiC\sSoftware\sVersion:\s(.*)', show_version_output, re.IGNORECASE).group(1)
    return sonic_ver


@pytest.fixture(scope='session')
def engines(topology_obj):
    engines_data = DottedDict()
    engines_data.dut = topology_obj.players['dut']['engine']
    engines_data.ha = topology_obj.players['ha']['engine']
    engines_data.hb = topology_obj.players['hb']['engine']
    return engines_data


@pytest.fixture(scope='session')
def interfaces(topology_obj):
    interfaces_data = DottedDict()
    interfaces_data.ha_dut_1 = topology_obj.ports['ha-dut-1']
    interfaces_data.ha_dut_2 = topology_obj.ports['ha-dut-2']
    interfaces_data.hb_dut_1 = topology_obj.ports['hb-dut-1']
    interfaces_data.hb_dut_2 = topology_obj.ports['hb-dut-2']
    interfaces_data.dut_ha_1 = topology_obj.ports['dut-ha-1']
    interfaces_data.dut_ha_2 = topology_obj.ports['dut-ha-2']
    interfaces_data.dut_hb_1 = topology_obj.ports['dut-hb-1']
    interfaces_data.dut_hb_2 = topology_obj.ports['dut-hb-2']
    return interfaces_data


@pytest.fixture(scope='session')
def platform_params(platform, hwsku, setup_name):
    """
    Method for getting all platform related data
    :return: dictionary with platform data
    """
    platform_data = DottedDict()
    platform_data.platform = platform
    platform_data.hwsku = hwsku
    platform_data.setup_name = setup_name
    return platform_data


@pytest.fixture(scope="session")
def upgrade_params(base_version, target_version, wjh_deb_url):
    """
    Method for getting all upgrade related parameters
    :return: dictionary with upgrade parameters
    """
    upgrade_data = DottedDict()

    upgrade_data.base_version = base_version
    upgrade_data.target_version = target_version
    upgrade_data.wjh_deb_url = wjh_deb_url
    upgrade_data.is_upgrade_required = False
    if base_version and target_version:
        upgrade_data.is_upgrade_required = True
    else:
        logger.info('Either one or all the upgrade arguments is missing, skipping the upgrade flow')
    return upgrade_data


@pytest.fixture(scope="session")
def players(topology_obj):
    return topology_obj.players

