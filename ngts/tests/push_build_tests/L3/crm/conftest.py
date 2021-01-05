import allure
import pytest
from retry.api import retry_call


@pytest.fixture(scope='module')
def env(topology_obj):
    """ Fixture which contains DUT - engine and CLI objects """
    class Collector:
        pass
    Collector.dut_engine = topology_obj.players['dut']['engine']
    Collector.sonic_cli = topology_obj.players['dut']['cli']
    Collector.vlan_iface_69 = 'Vlan69'
    Collector.vlan_iface_40 = 'Vlan40'
    Collector.ip_neigh_69 = '69.0.0.5'
    Collector.ip_neigh_40 = '40.0.0.5'
    Collector.dst_ip = '2.2.2.0'
    Collector.mask = 24
    yield Collector


@pytest.fixture(scope='module', autouse=True)
def set_polling_interval(env):
    """ Set CRM polling interval to 1 second """
    wait_time = 2
    polling_1_sec = 1
    original_poll_interval = env.sonic_cli.crm.get_polling_interval(env.dut_engine)

    with allure.step('Set CRM polling interval to {}'.format(polling_1_sec)):
        env.sonic_cli.crm.set_polling_interval(env.dut_engine, polling_1_sec)
    retry_call(ensure_polling_configured, fargs=[polling_1_sec, env.sonic_cli, env.dut_engine], tries=5, delay=1,
               logger=None)

    yield

    with allure.step('Restore CRM polling interval to {}'.format(original_poll_interval)):
        env.sonic_cli.crm.set_polling_interval(env.dut_engine, original_poll_interval)
    retry_call(ensure_polling_configured, fargs=[original_poll_interval, env.sonic_cli, env.dut_engine], tries=5,
               delay=1, logger=None)


@pytest.fixture
def cleanup(request):
    """
    Fixture executes cleanup commands on DUT after each of test case if such were provided
    """
    params_list = []
    yield params_list
    if not request.node.rep_call.passed and not request.node.rep_call.skipped:
        with allure.step('Execute test cleanup commands'):
            for item in params_list:
                item[0](*item[1:])


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """ This fixture call is required for 'cleanup' fixture """
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()


    setattr(item, "rep_" + rep.when, rep)


def ensure_polling_configured(expected_interval, sonic_cli, dut_engine):
    """
    Function checks that crm polling interval was configured
    """
    assert (sonic_cli.crm.get_polling_interval(dut_engine) == expected_interval), "CRM polling interval was not updated"
