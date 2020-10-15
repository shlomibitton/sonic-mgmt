import allure
import logging
import pytest
import time

from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker


logger = logging.getLogger()
CRM_UPDATE_TIME = 4


@pytest.fixture(scope='module', autouse=True)
def set_polling_interval(topology_obj):
    """ Set CRM polling interval to 1 second """
    wait_time = 2
    polling_1_sec = 1
    get_polling_interval = "crm show summary | awk '{print $3}'"
    set_polling_invetrval = "crm config polling interval {}"
    dut_engine = topology_obj.players['dut']['engine']
    legacy_polling_interval = dut_engine.run_cmd(get_polling_interval).strip()

    with allure.step('Set CRM polling interval to {}'.format(polling_1_sec)):
        dut_engine.run_cmd(set_polling_invetrval.format(polling_1_sec))
    time.sleep(wait_time)
    yield
    with allure.step('Restore CRM polling interval to {}'.format(legacy_polling_interval)):
        dut_engine.run_cmd(set_polling_invetrval.format(legacy_polling_interval))


@pytest.fixture
def cleanup(topology_obj):
    """
    Fixture executes cleanup commands on DUT after each of test case if such were provided
    """
    cmd_list = []
    yield cmd_list

    dut_engine = topology_obj.players['dut']['engine']
    with allure.step('Execute test cleanup commands'):
        for cmd in cmd_list:
            dut_engine.run_cmd(cmd)


def get_crm_stat(dut_engine, ip_ver):
    """
    Function gets crm counters of ipv4/6 route resource
    """
    cmd = "crm show resources ipv{ip_ver} route | grep ipv{ip_ver}_route".format(ip_ver=ip_ver)
    out = dut_engine.run_cmd(cmd)
    used, available = [int(item) for item in out.split()[1:]]
    return used, available


@pytest.mark.push_gate
def test_crm_show_res(topology_obj):
    """
    Run PushGate CRM test case, test doing verification of crm show commands
    """
    cmd_template = "crm show resources ipv{ip_ver} {res_type} | grep {res_type}"
    res_list = ["neighbor", "nexthop", "route"]

    dut_engine = topology_obj.players['dut']['engine']
    with allure.step('Verify crm show commands'):
        for ip_ver in [4, 6]:
            for crm_res in res_list:
                res_type, used, available = dut_engine.run_cmd(cmd_template.format(ip_ver=ip_ver, res_type=crm_res)).split()
                assert used.isdigit(), "Used counter of {} resource is not integer: {}".format(res_type, used)
                assert available.isdigit(), "Available counter of {} resource is not integer: {}".format(res_type, available)


@pytest.mark.push_gate
@pytest.mark.parametrize("ip_ver,add_route,del_route", [("4", "ip route add 2.2.2.0/24 dev {}",
                                                                "ip route del 2.2.2.0/24 dev {}"),
                                                                ("6", "ip -6 route add 2001::/126 dev {}",
                                                                "ip -6 route del 2001::/126 dev {}")],
                                                                ids=["ipv4", "ipv6"])
@allure.title('PushGate CRM test case')
def test_crm_route(topology_obj, cleanup, ip_ver, add_route, del_route):
    """
    Run PushGate CRM test case, test doing verification of 'used' and 'available' CRM counters for IPv4/6 route
    """
    dut_engine = topology_obj.players['dut']['engine']
    vlan_iface = 'Vlan31'
    add_route = 'sudo ' + add_route.format(vlan_iface)
    del_route = 'sudo ' + del_route.format(vlan_iface)

    route_used, route_available = get_crm_stat(dut_engine, ip_ver)

    with allure.step('Add route: {}'.format(add_route)):
        # Add route
        dut_engine.run_cmd(add_route)

    # Make sure CRM counters updated
    time.sleep(CRM_UPDATE_TIME)

    with allure.step('Get CRM route counters'):
        new_route_used, new_route_available = get_crm_stat(dut_engine, ip_ver)

    with allure.step('Verify CRM used and available counters'):
        # Verify used and available counters
        if not (new_route_used - route_used == 1):
            cleanup.append(del_route)
            pytest.fail('CRM counter for used IPv{} route was not incremented: original {}; new {}'.format(ip_ver,
                        route_used, new_route_used))
        if not (route_available - new_route_available >= 1):
            cleanup.append(del_route)
            pytest.fail('CRM counter for available IPv{} route was not incremented: original {}; new {}'.format(ip_ver,
                        route_available, new_route_available))

    with allure.step('Remove route: {}'.format(del_route)):
        # Remove route
        dut_engine.run_cmd(del_route)

    # Make sure CRM counters updated
    time.sleep(CRM_UPDATE_TIME)

    new_route_used, new_route_available = get_crm_stat(dut_engine, ip_ver)

    with allure.step('Verify CRM used and available counters'):
        # Verify used and available counters
        if not (new_route_used == route_used):
            pytest.fail('CRM counter for used IPv{} route was restored: {} != {}'.format(ip_ver,
                        route_used, new_route_used))
        if not (route_available == new_route_available):
            pytest.fail('CRM counter for available IPv{} route was not restored: {} != {}'.format(ip_ver,
                        route_available, new_route_available))
