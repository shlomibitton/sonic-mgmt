import allure
import logging
import pytest

from ngts.config_templates.vlan_config_template import vlan_configuration
from ngts.config_templates.ip_config_template import ip_configuration
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

logger = logging.getLogger()

# Dict below will be send to test as parameters
vlan = {
    'dut': [{'vlan_id': 5, 'vlan_members': ['dut-hb-1'], 'mode': 'trunk'},
            {'vlan_id': 6, 'vlan_members': ['dut-hb-1'], 'mode': 'trunk'},
            {'vlan_id': 7, 'vlan_members': ['dut-hb-1'], 'mode': 'trunk'},
            {'vlan_id': 8, 'vlan_members': ['dut-hb-1'], 'mode': 'trunk'},
            {'vlan_id': 9, 'vlan_members': ['dut-hb-1'], 'mode': 'trunk'}],
    'hb': [{'vlan_id': 5, 'vlan_members': ['hb-dut-1']},
           {'vlan_id': 6, 'vlan_members': ['hb-dut-1']},
           {'vlan_id': 7, 'vlan_members': ['hb-dut-1']},
           {'vlan_id': 8, 'vlan_members': ['hb-dut-1']},
           {'vlan_id': 9, 'vlan_members': ['hb-dut-1']}]
}

ip = {
    'dut': [{'iface': 'Vlan', 'iface_type': 'vlan', 'vlan_id': 5, 'ips': [('1.1.1.1', '24')]},
            {'iface': 'Vlan', 'iface_type': 'vlan', 'vlan_id': 6, 'ips': [('2.2.2.1', '24')]},
            {'iface': 'Vlan', 'iface_type': 'vlan', 'vlan_id': 7, 'ips': [('3.3.3.1', '24')]},
            {'iface': 'Vlan', 'iface_type': 'vlan', 'vlan_id': 8, 'ips': [('4.4.4.1', '24')]},
            {'iface': 'Vlan', 'iface_type': 'vlan', 'vlan_id': 9, 'ips': [('5.5.5.1', '24')]}
            ],
    'hb': [{'iface': 'hb-dut-1', 'iface_type': 'vlan', 'vlan_id': 5, 'ips': [('1.1.1.2', '24')]},
           {'iface': 'hb-dut-1', 'iface_type': 'vlan', 'vlan_id': 6, 'ips': [('2.2.2.2', '24')]},
           {'iface': 'hb-dut-1', 'iface_type': 'vlan', 'vlan_id': 7, 'ips': [('3.3.3.2', '24')]},
           {'iface': 'hb-dut-1', 'iface_type': 'vlan', 'vlan_id': 8, 'ips': [('4.4.4.2', '24')]},
           {'iface': 'hb-dut-1', 'iface_type': 'vlan', 'vlan_id': 9, 'ips': [('5.5.5.2', '24')]}
           ]
}

test_args = {'vlan': vlan, 'ip': ip}


@pytest.mark.vlan
@pytest.mark.parametrize('configuration_dict', [test_args])
@allure.title('Basic VLAN test case')
def test_vlan_basic(topology_obj, vlan_configuration, ip_configuration, configuration_dict):
    """
    Run basic test for VLANs. In this test case we will create 5 VLANs on DUT and host with IPs and then do ping from
    host to vlan interfaces IPs on DUT
    """
    try:
        # TODO: hardcoded validation params
        sender_host = 'hb'
        vlans = [5, 6, 7, 8, 9]
        ips = ['1.1.1.1', '2.2.2.1', '3.3.3.1', '4.4.4.1', '5.5.5.1']
        iface = 'hb-dut-1'

        for vlan_ip in zip(vlans, ips):
            with allure.step('Performing VLAN validation - send ping to interface in VLAN {}'.format(vlan_ip[0])):
                src_vlan_iface = '{}.{}'.format(topology_obj.ports[iface], vlan_ip[0])
                dst_ip = vlan_ip[1]
                # Here we do ping from HB to IPs on DUT in VLAN ifaces
                validation = {'sender': sender_host, 'args': {'iface': src_vlan_iface, 'count': 3, 'dst': dst_ip}}
                ping = PingChecker(topology_obj.players, validation)
                logger.info('Checking that possible to ping VLAN: {} ip address: {}'.format(vlan, vlan_ip))
                ping.run_validation()

    except Exception as err:
        raise AssertionError(err)
