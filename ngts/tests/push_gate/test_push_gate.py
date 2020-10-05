import allure
import logging
import pytest

from ngts.cli_wrappers.linux_mac_clis import get_mac_address
from ngts.cli_wrappers.sonic_mac_clis import show_mac
from ngts.cli_wrappers.sonic_lldp_clis import parse_lldp_info_for_specific_interface
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

logger = logging.getLogger()

# Test configs - dicts below will be used for configure vlan and ip for tests
vlan = {
    'dut': [{'vlan_id': 5, 'vlan_members': ['dut-ha-1'], 'mode': 'trunk'}],
    'ha': [{'vlan_id': 5, 'vlan_members': ['ha-dut-1']}]
}
ip = {
    'dut': [{'iface': 'Vlan', 'iface_type': 'vlan', 'vlan_id': 5, 'ips': [('1.1.1.1', '24')]}],
    'ha': [{'iface': 'ha-dut-1', 'iface_type': 'vlan', 'vlan_id': 5, 'ips': [('1.1.1.2', '24')]}]
}


@pytest.mark.push_gate
@allure.title('PushGate VLAN test case')
def test_push_gate_vlan(topology_obj):
    """
    Run PushGate VLAN test case
    """
    try:
        # TODO validation is hardcodded
        host_name = 'ha'
        host_port = topology_obj.ports['ha-dut-1']
        vlan = 5
        host_vlan_iface = '{}.{}'.format(host_port, vlan)
        dut_ip = '1.1.1.1'

        with allure.step('Sending 3 ping packets in VLAN 5 to DUT'):
            validation = {'sender': host_name, 'args': {'iface': host_vlan_iface, 'count': 3, 'dst': dut_ip}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Doing ping in VLAN: {} for IP address: {}'.format(vlan, dut_ip))
            ping.run_validation()

    except Exception as err:
        raise AssertionError(err)


@pytest.mark.push_gate
@allure.title('PushGate FDB test case')
def test_push_gate_fdb(topology_obj):
    """
    Run PushGate FDB test case
    """
    try:
        # TODO validation is hardcodded
        dut_engine = topology_obj.players['dut']['engine']
        host_engine = topology_obj.players['ha']['engine']
        host_port = topology_obj.ports['ha-dut-1']
        ha_dut_1_mac = get_mac_address(host_engine, host_port)
        logger.info('Checking that host mac address in FDB output')
        assert str(ha_dut_1_mac).upper() in show_mac(dut_engine)

    except Exception as err:
        raise AssertionError(err)


@pytest.mark.push_gate
@allure.title('PushGate LLDP test case')
def test_push_gate_lldp(topology_obj):
    """
    Run PushGate LLDP test case
    """
    try:
        # TODO validation is hardcodded
        ports_for_validation = {'host_ports': ['ha-dut-1', 'ha-dut-2', 'hb-dut-1', 'hb-dut-2'],
                                'dut_ports': ['dut-ha-1', 'dut-ha-2', 'dut-hb-1', 'dut-hb-2']}

        dut_engine = topology_obj.players['dut']['engine']
        for host_dut_port in zip(ports_for_validation['host_ports'], ports_for_validation['dut_ports']):
            host_port_alias = host_dut_port[0]
            host_name_alias = host_port_alias.split('-')[0]
            host_engine = topology_obj.players[host_name_alias]['engine']
            host_port_mac = get_mac_address(host_engine, topology_obj.ports[host_port_alias])
            dut_port = topology_obj.ports[host_dut_port[1]]
            with allure.step('Checking peer MAC address via LLDP in interface {}'.format(dut_port)):
                lldp_info = parse_lldp_info_for_specific_interface(dut_engine, dut_port)
                logger.info('Checking that peer device mac address in LLDP output')
                assert host_port_mac in lldp_info['Chassis']['ChassisID']

    except Exception as err:
        raise AssertionError(err)
