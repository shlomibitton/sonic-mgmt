import allure
import logging
import pytest

from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

logger = logging.getLogger()


@pytest.mark.push_gate
@allure.title('PushGate VLAN test case')
def test_push_gate_vlan(topology_obj):
    """
    Run PushGate VLAN test case, test doing PING to VLAN interfaces IPs from host to DUT
    """
    try:
        host_name = 'ha'
        host_port = topology_obj.ports['ha-dut-2']
        vlans = [500, 600]
        dst_ips = ['50.0.0.1', '60.0.0.1']

        for dst_ip, vlan in zip(dst_ips, vlans):
            host_vlan_iface = '{}.{}'.format(host_port, vlan)
            with allure.step('Sending 3 ping packets in VLAN {} to {}'.format(vlan, dst_ip)):
                validation = {'sender': host_name, 'args': {'iface': host_vlan_iface, 'count': 3, 'dst': dst_ip}}
                ping = PingChecker(topology_obj.players, validation)
                logger.info('Doing ping in VLAN: {} for IP address: {}'.format(vlan, dst_ip))
                ping.run_validation()

    except Exception as err:
        raise AssertionError(err)
