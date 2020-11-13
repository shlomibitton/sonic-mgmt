import allure
import logging
import pytest
import time


logger = logging.getLogger()
CRM_UPDATE_TIME = 4


@pytest.fixture(scope='module', autouse=True)
def set_polling_interval(topology_obj):
    """ Set CRM polling interval to 1 second """
    wait_time = 2
    polling_1_sec = 1
    dut_engine = topology_obj.players['dut']['engine']
    sonic_cli = topology_obj.players['dut']['cli']
    legacy_polling_interval = sonic_cli.crm.get_polling_interval(dut_engine)

    with allure.step('Set CRM polling interval to {}'.format(polling_1_sec)):
        sonic_cli.crm.set_polling_interval(dut_engine, polling_1_sec)
    time.sleep(wait_time)

    yield

    with allure.step('Restore CRM polling interval to {}'.format(legacy_polling_interval)):
        sonic_cli.crm.set_polling_interval(dut_engine, legacy_polling_interval)


@pytest.fixture
def cleanup(topology_obj):
    """
    Fixture executes cleanup commands on DUT after each of test case if such were provided
    """
    params_list = []
    yield params_list

    sonic_cli = topology_obj.players['dut']['cli']
    with allure.step('Execute test cleanup commands'):
        for param in params_list:
            sonic_cli.route.del_route(*param)


def get_crm_stat(dut_engine, sonic_cli, ip_ver):
    """
    Function gets crm counters of ipv4/6 route resource
    """
    crm_res_all = sonic_cli.crm.parse_resources_table(dut_engine)
    route_res = crm_res_all['main_resources']['ipv{}_route'.format(ip_ver)]

    return route_res['used'], route_res['available']


@pytest.mark.push_gate
def test_crm_show_res(topology_obj):
    """
    Run PushGate CRM test case, test doing verification of crm show commands
    """
    dut_engine = topology_obj.players['dut']['engine']
    sonic_cli = topology_obj.players['dut']['cli']

    crm_res_all = sonic_cli.crm.parse_resources_table(dut_engine)

    with allure.step('Verify crm show commands'):
        for res_type, value in crm_res_all['main_resources'].items():
            assert isinstance(value['used'], int), "Used counter of {} resource is not integer: {}".format(
                res_type, value['used']
            )
            assert isinstance(value['available'], int), "Available counter of {} resource is not integer: {}".format(
                res_type, value['available']
            )


@pytest.mark.push_gate
@pytest.mark.parametrize('ip_ver,dst,mask', [('4', '2.2.2.0', 24), ('6', '2001::', 126)], ids=['ipv4', 'ipv6'])
@allure.title('PushGate CRM test case')
def test_crm_route(topology_obj, cleanup, ip_ver, dst, mask):
    """
    Run PushGate CRM test case, test doing verification of 'used' and 'available' CRM counters for IPv4/6 route
    """
    dut_engine = topology_obj.players['dut']['engine']
    sonic_cli = topology_obj.players['dut']['cli']
    vlan_iface = 'Vlan31'

    route_used, route_available = get_crm_stat(dut_engine, sonic_cli, ip_ver)

    with allure.step('Add route: {}/{} {}'.format(dst, mask, vlan_iface)):
        # Add route
        sonic_cli.route.add_route(dut_engine, dst, vlan_iface, mask)

    # Make sure CRM counters updated
    time.sleep(CRM_UPDATE_TIME)

    with allure.step('Get CRM route counters'):
        new_route_used, new_route_available = get_crm_stat(dut_engine, sonic_cli, ip_ver)

    with allure.step('Verify CRM used and available counters'):
        # Verify used and available counters
        if not (new_route_used - route_used == 1):
            cleanup.append((dut_engine, dst, vlan_iface, mask))
            pytest.fail('CRM counter for used IPv{} route was not incremented: original {}; new {}'.format(ip_ver,
                        route_used, new_route_used))
        if not (route_available - new_route_available >= 1):
            cleanup.append((dut_engine, dst, vlan_iface, mask))
            pytest.fail('CRM counter for available IPv{} route was not incremented: original {}; new {}'.format(ip_ver,
                        route_available, new_route_available))

    with allure.step('Remove route: {}/{} {}'.format(dst, mask, vlan_iface)):
        # Remove route
        sonic_cli.route.del_route(dut_engine, dst, vlan_iface, mask)

    # Make sure CRM counters updated
    time.sleep(CRM_UPDATE_TIME)

    new_route_used, new_route_available = get_crm_stat(dut_engine, sonic_cli, ip_ver)

    with allure.step('Verify CRM used and available counters'):
        # Verify used and available counters
        if not (new_route_used == route_used):
            pytest.fail('CRM counter for used IPv{} route was restored: {} != {}'.format(ip_ver,
                        route_used, new_route_used))
        if not (route_available == new_route_available):
            pytest.fail('CRM counter for available IPv{} route was not restored: {} != {}'.format(ip_ver,
                        route_available, new_route_available))
