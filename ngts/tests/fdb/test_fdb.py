import allure
import logging
import pytest

from ngts.cli_wrappers.linux_mac_clis import get_mac_address
from ngts.cli_wrappers.sonic_mac_clis import show_mac
from ngts.config_templates.vlan_config_template import vlan_configuration
from ngts.config_templates.ip_config_template import ip_configuration
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

logger = logging.getLogger()

# Dict below will be send to test as parameters
vlan = {
    'dut': [{'vlan_id': 5, 'vlan_members': ['dut-hb-1'], 'mode': 'trunk'}],
    'hb': [{'vlan_id': 5, 'vlan_members': ['hb-dut-1']}]
}

ip = {
    'dut': [{'iface': 'Vlan', 'iface_type': 'vlan', 'vlan_id': 5, 'ips': [('1.1.1.1', '24')]},],
    'hb': [{'iface': 'hb-dut-1', 'iface_type': 'vlan', 'vlan_id': 5, 'ips': [('1.1.1.2', '24')]}]
}

test_args = {'vlan': vlan, 'ip': ip}


@pytest.mark.fdb
@pytest.mark.parametrize('configuration_dict', [test_args])
@allure.title('Basic FDB test case')
def test_fdb_basic(topology_obj, vlan_configuration, ip_configuration, configuration_dict):
    """
    Run basic fdb test
    """
    try:
        # TODO validation is hardcodded
        dut_engine = topology_obj.players['dut']['engine']
        host_name = 'hb'
        host_engine = topology_obj.players[host_name]['engine']
        host_port = topology_obj.ports['hb-dut-1']
        vlan = 5
        host_vlan_iface = '{}.{}'.format(host_port, vlan)
        dut_ip = '1.1.1.1'

        with allure.step('Sending 3 ping packets to host for update FDB'):
            validation = {'sender': host_name, 'args': {'iface': host_vlan_iface, 'count': 3, 'dst': dut_ip}}
            ping = PingChecker(topology_obj.players, validation)
            ping.run_validation()

        hb_dut_1_mac = get_mac_address(host_engine, host_port)
        logger.info('Checking that host mac address are in FDB table')
        assert str(hb_dut_1_mac).upper() in show_mac(dut_engine)

    except Exception as err:
        raise AssertionError(err)
